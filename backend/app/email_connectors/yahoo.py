import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import socket
import logging

logger = logging.getLogger(__name__)

class YahooConnector:
    """Yahoo Mail IMAP connector for fetching emails"""
    
    IMAP_SERVER = "imap.mail.yahoo.com"
    IMAP_PORT = 993
    IMAP_TIMEOUT = 600  # 10 minutes timeout for IMAP operations (increased for large batches)
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize with email and app password
        Note: Yahoo requires app-specific password, not regular password
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None
    
    def _connect(self):
        """Establish IMAP connection with timeout"""
        if self.imap is None:
            try:
                # Set socket timeout before connecting
                socket.setdefaulttimeout(self.IMAP_TIMEOUT)
                self.imap = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT, timeout=self.IMAP_TIMEOUT)
                logger.info(f"Connecting to Yahoo IMAP for {self.email_address}")
                self.imap.login(self.email_address, self.app_password)
                logger.info(f"Successfully connected to Yahoo IMAP")
            except socket.timeout:
                logger.error(f"Timeout connecting to Yahoo IMAP")
                raise Exception("Connection to Yahoo Mail timed out. Please check your network connection and try again.")
            except Exception as e:
                logger.error(f"Error connecting to Yahoo IMAP: {e}")
                raise
    
    def _disconnect(self):
        """Close IMAP connection"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
            self.imap = None
    
    def fetch_emails_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        max_results: int = 5000
    ) -> List[Dict]:
        """
        Fetch emails within date range using IMAP UID (stable identifier)
        Returns list of email metadata dicts
        
        Uses UID instead of sequence numbers because:
        - UIDs are stable and don't change when emails are deleted
        - Prevents duplicate email issues when re-analyzing date ranges
        """
        self._connect()
        
        try:
            logger.info(f"Selecting INBOX for {self.email_address}")
            self.imap.select('INBOX')
            
            # Format dates for IMAP search
            start_str = start_date.strftime("%d-%b-%Y")
            end_str = end_date.strftime("%d-%b-%Y")
            search_query = f'(SINCE {start_str} BEFORE {end_str})'
            
            logger.info(f"Searching for emails from {start_str} to {end_str}")
            # Use UID search instead of regular search for stable identifiers
            # Set timeout for search operation
            try:
                status, message_uids = self.imap.uid('SEARCH', None, search_query)
            except socket.timeout:
                logger.error(f"Timeout during IMAP search for date range {start_str} to {end_str}")
                raise Exception(f"Search timed out. The date range may be too large or Yahoo Mail is slow. Try a smaller date range.")
            
            if status != 'OK':
                raise Exception(f"IMAP UID search failed: {status}")
            
            if not message_uids[0]:
                logger.info(f"No emails found in date range {start_str} to {end_str}")
                return []
            
            email_uids = message_uids[0].split()
            total_found = len(email_uids)
            logger.info(f"Found {total_found} emails in date range, limiting to {max_results}")
            print(f"[PRINT] Found {total_found} emails, processing...")
            
            emails = []
            
            # Limit results
            email_uids = email_uids[:max_results] if len(email_uids) > max_results else email_uids
            
            # Process emails with progress logging
            logger.info(f"Starting to process {len(email_uids)} emails...")
            print(f"[PRINT] Processing {len(email_uids)} emails...")
            
            # Process in smaller batches to avoid timeouts
            # Use smaller batches (50) for better progress tracking and timeout recovery
            batch_size = 50
            
            for batch_start in range(0, len(email_uids), batch_size):
                batch_end = min(batch_start + batch_size, len(email_uids))
                batch_uids = email_uids[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//batch_size + 1}: emails {batch_start+1}-{batch_end} of {len(email_uids)}")
                print(f"[PRINT] Processing batch {batch_start//batch_size + 1}: {batch_start+1}-{batch_end}/{len(email_uids)}")
                
                # Refresh connection every few batches to avoid stale connections
                if batch_start > 0 and batch_start % (batch_size * 3) == 0:
                    logger.info("Refreshing IMAP connection...")
                    try:
                        self._disconnect()
                        self._connect()
                        self.imap.select('INBOX')
                    except Exception as e:
                        logger.warning(f"Error refreshing connection: {e}, continuing with existing connection")
                
                for idx, email_uid in enumerate(batch_uids):
                    global_idx = batch_start + idx
                    if global_idx > 0 and global_idx % 25 == 0:
                        logger.info(f"Processed {global_idx}/{len(email_uids)} emails...")
                        print(f"[PRINT] Processed {global_idx}/{len(email_uids)} emails...")
                    
                    try:
                        # Use UID fetch to get only headers (much faster than full RFC822)
                        # Set a shorter timeout per email (10 seconds) to avoid hanging
                        original_timeout = socket.getdefaulttimeout()
                        try:
                            socket.settimeout(10)  # 10 second timeout per email fetch
                            # Fetch only headers instead of full email body for better performance
                            status, msg_data = self.imap.uid('FETCH', email_uid, '(BODY.PEEK[HEADER])')
                        except socket.timeout:
                            logger.warning(f"Timeout fetching email UID {email_uid} (email {global_idx+1}), skipping")
                            print(f"[PRINT] Timeout on email {global_idx+1}, skipping")
                            continue
                        except Exception as e:
                            logger.warning(f"Error fetching email UID {email_uid} (email {global_idx+1}): {e}, skipping")
                            print(f"[PRINT] Error on email {global_idx+1}: {e}, skipping")
                            continue
                        finally:
                            # Restore original timeout
                            socket.settimeout(original_timeout)
                        
                        if status != 'OK' or not msg_data or not msg_data[0]:
                            continue
                        
                        # Parse headers only (no body needed for metadata)
                        # IMAP response structure: [(b'1 (BODY[HEADER] {1234}', b'headers...'), b')']
                        try:
                            header_data = msg_data[0]
                            if isinstance(header_data, tuple):
                                # Tuple format: (response_string, headers_bytes)
                                raw_headers = header_data[1] if len(header_data) > 1 else header_data[0]
                            elif isinstance(header_data, list):
                                # List format: [response_string, headers_bytes, ...]
                                raw_headers = header_data[1] if len(header_data) > 1 else header_data[0]
                            else:
                                raw_headers = header_data
                            
                            if isinstance(raw_headers, bytes):
                                msg = email.message_from_bytes(raw_headers)
                            elif isinstance(raw_headers, str):
                                msg = email.message_from_string(raw_headers)
                            else:
                                # Try to convert to bytes
                                raw_headers = bytes(str(raw_headers), 'utf-8')
                                msg = email.message_from_bytes(raw_headers)
                        except Exception as e:
                            logger.warning(f"Error parsing headers for UID {email_uid} (email {global_idx+1}): {e}, skipping")
                            print(f"[PRINT] Parse error on email {global_idx+1}: {e}, skipping")
                            continue
                        
                        # Extract headers
                        subject = self._decode_header(msg.get('Subject', ''))
                        from_header = msg.get('From', '')
                        date_str = msg.get('Date', '')
                        
                        # Try to get Message-ID header as additional identifier (more stable)
                        message_id_header = msg.get('Message-ID', '')
                        
                        # Parse date
                        try:
                            date_tuple = email.utils.parsedate_tz(date_str)
                            if date_tuple:
                                date_received = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                            else:
                                date_received = datetime.now()
                        except:
                            date_received = datetime.now()
                        
                        # Extract sender
                        sender_email = self._extract_email(from_header)
                        sender_name = self._extract_name(from_header)
                        
                        # Use UID as message_id (stable identifier)
                        # Prefer Message-ID header if available, otherwise use UID
                        uid_str = email_uid.decode() if isinstance(email_uid, bytes) else str(email_uid)
                        if message_id_header:
                            # Use Message-ID header if available (most stable)
                            # Format: yahoo_uid_<uid>_msgid_<message_id>
                            # This ensures uniqueness even if Message-ID is missing angle brackets
                            msg_id_clean = message_id_header.strip('<>')
                            message_id = f"yahoo_uid_{uid_str}_msgid_{msg_id_clean}"
                        else:
                            # Fallback to UID with prefix to distinguish from old sequence numbers
                            message_id = f"yahoo_uid_{uid_str}"
                        
                        emails.append({
                            'message_id': message_id,
                            'sender_email': sender_email,
                            'sender_name': sender_name,
                            'subject': subject,
                            'date_received': date_received,
                            'thread_id': None,  # IMAP doesn't provide thread ID easily
                            'snippet': self._get_snippet(msg)
                        })
                        
                    except Exception as e:
                        uid_str = email_uid.decode() if isinstance(email_uid, bytes) else str(email_uid)
                        logger.warning(f"Error processing email UID {uid_str} (email {global_idx+1}): {e}, skipping")
                        print(f"[PRINT] Error processing email {global_idx+1}: {e}, skipping")
                        continue
            
            logger.info(f"Successfully fetched {len(emails)} emails from date range {start_str} to {end_str}")
            return emails
            
        except socket.timeout as e:
            logger.error(f"Timeout during email fetch: {e}")
            raise Exception(f"Request timed out while fetching emails. The date range may be too large. Try analyzing a smaller date range.")
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise
        finally:
            self._disconnect()
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        decoded_parts = decode_header(header)
        decoded_str = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += part
        return decoded_str
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
        return match.group(0) if match else from_header
    
    def _extract_name(self, from_header: str) -> Optional[str]:
        """Extract sender name from From header"""
        match = re.match(r'^(.+?)\s*<[\w\.-]+@[\w\.-]+\.\w+>', from_header)
        if match:
            name = match.group(1).strip().strip('"\'')
            return name if name else None
        return None
    
    def _get_snippet(self, msg: email.message.Message) -> str:
        """Extract text snippet from email"""
        # Since we're only fetching headers, we can't get the body snippet
        # Return empty string or use subject as snippet
        try:
            subject = msg.get('Subject', '')
            if subject:
                decoded_subject = self._decode_header(subject)
                return decoded_subject[:200] if decoded_subject else ""
        except:
            pass
        return ""


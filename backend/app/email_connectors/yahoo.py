import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

class YahooConnector:
    """Yahoo Mail IMAP connector for fetching emails"""
    
    IMAP_SERVER = "imap.mail.yahoo.com"
    IMAP_PORT = 993
    
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize with email and app password
        Note: Yahoo requires app-specific password, not regular password
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None
    
    def _connect(self):
        """Establish IMAP connection"""
        if self.imap is None:
            self.imap = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            self.imap.login(self.email_address, self.app_password)
    
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
        Fetch emails within date range
        Returns list of email metadata dicts
        """
        self._connect()
        
        try:
            self.imap.select('INBOX')
            
            # Format dates for IMAP search
            start_str = start_date.strftime("%d-%b-%Y")
            end_str = end_date.strftime("%d-%b-%Y")
            search_query = f'(SINCE {start_str} BEFORE {end_str})'
            
            # Search for emails
            status, message_ids = self.imap.search(None, search_query)
            
            if status != 'OK':
                raise Exception(f"IMAP search failed: {status}")
            
            email_ids = message_ids[0].split()
            emails = []
            
            # Limit results
            email_ids = email_ids[:max_results] if len(email_ids) > max_results else email_ids
            
            for email_id in email_ids:
                try:
                    status, msg_data = self.imap.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract headers
                    subject = self._decode_header(msg.get('Subject', ''))
                    from_header = msg.get('From', '')
                    date_str = msg.get('Date', '')
                    
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
                    
                    emails.append({
                        'message_id': email_id.decode() if isinstance(email_id, bytes) else str(email_id),
                        'sender_email': sender_email,
                        'sender_name': sender_name,
                        'subject': subject,
                        'date_received': date_received,
                        'thread_id': None,  # IMAP doesn't provide thread ID easily
                        'snippet': self._get_snippet(msg)
                    })
                    
                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    continue
            
            return emails
            
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
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode('utf-8', errors='ignore')[:200]
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='ignore')[:200]
        except:
            pass
        return ""


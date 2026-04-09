from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime
import logging

logger = logging.getLogger(__name__)

from app.range_semantics import half_open_contains_instant

# Per date-range fetch cap (analysis passes the default). Gmail queries can match far more than this.
DEFAULT_MAX_RESULTS_PER_RANGE = 250_000


def _gmail_query_half_open(start_date: datetime, end_date: datetime, exclude_sent: bool) -> str:
    """Gmail after:/before: are calendar dates; half-open [start, end) uses end as exclusive calendar day."""
    sa = start_date.strftime("%Y/%m/%d")
    eb = end_date.strftime("%Y/%m/%d")
    q = f"after:{sa} before:{eb}"
    if exclude_sent:
        q += " -in:sent"
    return q


class GmailConnector:
    """Gmail API connector for fetching emails"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, credentials_json: str):
        """
        Initialize with encrypted credentials JSON string
        """
        creds_dict = json.loads(credentials_json)
        self.credentials = Credentials.from_authorized_user_info(creds_dict)
        self._refresh_if_needed()
        self.service = build('gmail', 'v1', credentials=self.credentials)
    
    def _refresh_if_needed(self):
        """Refresh credentials if expired"""
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
            except RefreshError as e:
                # Token has been revoked or expired permanently
                error_msg = str(e)
                if 'invalid_grant' in error_msg or 'Token has been expired or revoked' in error_msg:
                    raise ValueError(
                        "Gmail OAuth token has been expired or revoked. "
                        "Please reconnect your Gmail account through the account management interface."
                    ) from e
                raise
    
    def get_email_count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        exclude_sent: bool = True
    ) -> int:
        """
        Get count of emails in date range without fetching them
        Returns the total count
        
        Args:
            exclude_sent: If True, excludes sent emails (only counts received emails)
        """
        query = _gmail_query_half_open(start_date, end_date, exclude_sent)
        
        try:
            total = 0
            page_token = None
            
            while True:
                request = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=500,
                    pageToken=page_token
                )
                response = request.execute()
                
                messages = response.get('messages', [])
                if not messages:
                    break
                
                for msg in messages:
                    try:
                        msg_detail = self.service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='metadata',
                            metadataHeaders=['Date']
                        ).execute()
                        dr = datetime.fromtimestamp(
                            int(msg_detail['internalDate']) / 1000.0,
                            tz=timezone.utc,
                        )
                        if half_open_contains_instant(dr, start_date, end_date):
                            total += 1
                    except Exception as e:
                        logger.warning(f"Error counting message {msg.get('id')}: {e}")
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return total
        except Exception as e:
            logger.error(f"Error getting email count: {e}")
            raise
    
    def fetch_emails_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        max_results: int = DEFAULT_MAX_RESULTS_PER_RANGE,
        progress_callback: callable = None,
        exclude_sent: bool = True
    ) -> List[Dict]:
        """
        Fetch emails within date range
        Returns list of email metadata dicts
        
        Args:
            max_results: Safety cap per fetch; if the query matches more, remaining messages are skipped
                (insights then reflect only what was ingested). Default is very large for full-mailbox runs.
            exclude_sent: If True, excludes sent emails (only fetches received emails)
        """
        query = _gmail_query_half_open(start_date, end_date, exclude_sent)
        
        emails = []
        page_token = None
        truncated = False
        
        try:
            while len(emails) < max_results:
                request = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(500, max_results - len(emails)),
                    pageToken=page_token
                )
                response = request.execute()
                
                next_page = response.get('nextPageToken')
                messages = response.get('messages', [])
                if not messages:
                    break
                
                # Batch fetch message details
                for msg in messages:
                    if len(emails) >= max_results:
                        break
                    
                    try:
                        msg_detail = self.service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='metadata',
                            metadataHeaders=['From', 'Subject', 'Date']
                        ).execute()
                        
                        headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}
                        
                        # Parse date (prefer internalDate for consistency with search window)
                        date_str = headers.get('Date', '')
                        try:
                            date_received = parsedate_to_datetime(date_str)
                        except Exception:
                            date_received = datetime.fromtimestamp(
                                int(msg_detail['internalDate']) / 1000.0,
                                tz=timezone.utc,
                            )
                        
                        if not half_open_contains_instant(date_received, start_date, end_date):
                            continue
                        
                        # Parse sender
                        from_header = headers.get('From', '')
                        sender_email = self._extract_email(from_header)
                        sender_name = self._extract_name(from_header)
                        
                        emails.append({
                            'message_id': msg['id'],
                            'sender_email': sender_email,
                            'sender_name': sender_name,
                            'subject': headers.get('Subject', ''),
                            'date_received': date_received,
                            'thread_id': msg_detail.get('threadId'),
                            'snippet': msg_detail.get('snippet', '')
                        })
                        
                        # Call progress callback every 25 emails
                        if progress_callback and len(emails) % 25 == 0:
                            try:
                                progress_callback(len(emails), max_results)
                            except Exception as e:
                                logger.warning("Progress callback failed: %s", e, exc_info=True)
                    except Exception as e:
                        logger.warning("Error fetching message %s: %s", msg["id"], e, exc_info=True)
                        continue
                
                if len(emails) >= max_results:
                    if next_page:
                        truncated = True
                    break
                page_token = next_page
                if not page_token:
                    break
                    
        except Exception as e:
            raise
        
        if truncated:
            logger.warning(
                "Gmail fetch for range %s–%s hit max_results=%s with more pages available. "
                "Insights use only ingested messages; raise max_results or use smaller date chunks.",
                start_date.date(),
                end_date.date(),
                max_results,
            )
        
        return emails
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        import re
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
        return match.group(0) if match else from_header
    
    def _extract_name(self, from_header: str) -> Optional[str]:
        """Extract sender name from From header"""
        import re
        # Try to extract name from "Name <email@domain.com>" format
        match = re.match(r'^(.+?)\s*<[\w\.-]+@[\w\.-]+\.\w+>', from_header)
        if match:
            name = match.group(1).strip().strip('"\'')
            return name if name else None
        return None
    
    @staticmethod
    def get_authorization_url(redirect_uri: str, client_id: str, client_secret: str) -> tuple[str, str]:
        """Get OAuth authorization URL and state"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=GmailConnector.SCOPES,
            redirect_uri=redirect_uri
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url, state
    
    @staticmethod
    def exchange_code_for_credentials(
        code: str, 
        redirect_uri: str, 
        client_id: str, 
        client_secret: str
    ) -> str:
        """Exchange authorization code for credentials JSON"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=GmailConnector.SCOPES,
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        return json.dumps({
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        })


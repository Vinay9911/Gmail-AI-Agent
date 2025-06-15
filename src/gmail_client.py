import os
import base64
import email
from email.mime.text import MIMEText
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger
from bs4 import BeautifulSoup
from config.settings import settings

class GmailClient:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        if os.path.exists(settings.gmail_token_path):
            creds = Credentials.from_authorized_user_file(
                settings.gmail_token_path, settings.gmail_scopes
            )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.gmail_credentials_path, settings.gmail_scopes
                )
                creds = flow.run_local_server(port=0)
            
            with open(settings.gmail_token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail authentication successful")
    
    def get_unread_messages(self, max_results: int = 10, since_time: Optional[float] = None) -> List[Dict]:
        """Get unread messages from Gmail received after since_time"""
        try:
            query = 'is:unread'
            if since_time is not None:
                query += f' after:{int(since_time)}'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            detailed_messages = []
            
            for message in messages:
                msg_detail = self.get_message_detail(message['id'])
                if msg_detail:
                    detailed_messages.append(msg_detail)
            
            logger.info(f"Retrieved {len(detailed_messages)} unread messages after {since_time}")
            return detailed_messages
            
        except HttpError as error:
            logger.error(f"Error retrieving messages: {error}")
            return []
    
    def get_message_detail(self, message_id: str) -> Optional[Dict]:
        """Get detailed message information"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            
            body = self.extract_message_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'body': body,
                'thread_id': message['threadId']
            }
            
        except HttpError as error:
            logger.error(f"Error getting message detail: {error}")
            return None
    
    def extract_message_body(self, payload) -> str:
        """Extract readable text from message payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    soup = BeautifulSoup(html_body, 'html.parser')
                    body = soup.get_text()
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body']['data']
                html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                soup = BeautifulSoup(html_body, 'html.parser')
                body = soup.get_text()
        
        return body.strip()
    
    def send_reply(self, thread_id: str, to_email: str, subject: str, body: str) -> bool:
        """Send a reply to an email"""
        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}"
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            send_message = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': thread_id
                }
            ).execute()
            
            logger.info(f"Reply sent successfully to {to_email}")
            return True
            
        except HttpError as error:
            logger.error(f"Error sending reply: {error}")
            return False
    
    def save_as_draft(self, thread_id: str, to_email: str, subject: str, body: str) -> bool:
        """Save a reply as draft for manual review"""
        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}"
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={
                    'message': {
                        'raw': raw_message,
                        'threadId': thread_id
                    }
                }
            ).execute()
            
            logger.info(f"Draft saved successfully for {to_email} (Draft ID: {draft['id']})")
            return True
            
        except HttpError as error:
            logger.error(f"Error saving draft: {error}")
            return False
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Message {message_id} marked as read")
            return True
            
        except HttpError as error:
            logger.error(f"Error marking message as read: {error}")
            return False
    
    def get_drafts(self, max_results: int = 10) -> List[Dict]:
        """Get list of draft messages"""
        try:
            results = self.service.users().drafts().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            drafts = results.get('drafts', [])
            detailed_drafts = []
            
            for draft in drafts:
                draft_detail = self.get_draft_detail(draft['id'])
                if draft_detail:
                    detailed_drafts.append(draft_detail)
            
            logger.info(f"Retrieved {len(detailed_drafts)} drafts")
            return detailed_drafts
            
        except HttpError as error:
            logger.error(f"Error retrieving drafts: {error}")
            return []
    
    def get_draft_detail(self, draft_id: str) -> Optional[Dict]:
        """Get detailed draft information"""
        try:
            draft = self.service.users().drafts().get(
                userId='me',
                id=draft_id
            ).execute()
            
            message = draft['message']
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            to_email = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipient')
            
            body = self.extract_message_body(message['payload'])
            
            return {
                'draft_id': draft_id,
                'message_id': message['id'],
                'subject': subject,
                'to': to_email,
                'body': body,
                'thread_id': message.get('threadId')
            }
            
        except HttpError as error:
            logger.error(f"Error getting draft detail: {error}")
            return None
    
    def send_draft(self, draft_id: str) -> bool:
        """Send a draft message"""
        try:
            sent_message = self.service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()
            
            logger.info(f"Draft {draft_id} sent successfully")
            return True
            
        except HttpError as error:
            logger.error(f"Error sending draft: {error}")
            return False
    
    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft message"""
        try:
            self.service.users().drafts().delete(
                userId='me',
                id=draft_id
            ).execute()
            
            logger.info(f"Draft {draft_id} deleted successfully")
            return True
            
        except HttpError as error:
            logger.error(f"Error deleting draft: {error}")
            return False
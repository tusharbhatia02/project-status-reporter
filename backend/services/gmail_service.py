# services/gmail_service.py
import os
import base64
import logging
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup



logger = logging.getLogger(__name__)
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] 

def get_project_emails(
    token_path: str,
    credentials_path: str,
    user_id: str = 'me',
    query: str = 'label:project-updates is:unread',
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieves and decodes recent, unread emails matching the query.
    Marks fetched emails as read. Requires token and credentials paths.
    """
    creds = None
    if not os.path.exists(token_path):
        logger.error(f"Gmail token file not found at {token_path}. Run scripts/gmail_auth.py.")
        return []
    if not os.path.exists(credentials_path):
         logger.error(f"Gmail credentials file not found at {credentials_path}.")
         return []

    try:
        creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)
    except Exception as e:
         logger.error(f"Failed to load credentials from {token_path}: {e}")
         return []

    if not creds or not creds.valid:
        
        logger.error(f"Invalid or expired credentials in {token_path}. Re-run scripts/gmail_auth.py.")
        return []

    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} emails matching query '{query}'.")
        if not messages: return []

        email_contents = []
        message_ids_to_mark_read = []
        for message_info in messages:
            message_id = message_info['id']
            try:
                msg = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')

                
                body_text = ""
                parts = payload.get('parts')
                if parts:
                    # Look for plain text first, then HTML
                    plain_part = next((p for p in parts if p.get('mimeType') == 'text/plain'), None)
                    html_part = next((p for p in parts if p.get('mimeType') == 'text/html'), None)
                    target_part = plain_part or html_part # Prioritize plain text

                    if target_part and target_part.get('body', {}).get('data'):
                        data = target_part['body']['data']
                        body_text = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8', errors='replace')
                        if target_part.get('mimeType') == 'text/html':
                             try:
                                 soup = BeautifulSoup(body_text, 'html.parser')
                                 body_text = soup.get_text(separator='\n', strip=True)
                             except Exception: # Handle potential BS4 errors
                                  logger.warning(f"Could not parse HTML body for email {message_id}, using raw.")
                    else: # Look deeper for nested parts if top-level fails (basic example)
                         if parts[0].get('parts'):
                              nested_part = parts[0]['parts'][0]
                              if nested_part.get('body', {}).get('data'):
                                   data = nested_part['body']['data']
                                   body_text = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8', errors='replace')


                elif payload.get('body', {}).get('data'): # No parts, try top-level body
                     data = payload['body']['data']
                     body_text = base64.urlsafe_b64decode(data.encode('UTF-8')).decode('UTF-8', errors='replace')

                email_contents.append({'id': message_id, 'sender': sender, 'subject': subject, 'body': body_text.strip()})
                message_ids_to_mark_read.append(message_id)

            except HttpError as error: logger.error(f'Error fetching email ID {message_id}: {error}')
            except Exception as e: logger.error(f'Error processing email ID {message_id}: {e}', exc_info=True)

        # Attempt to mark as read
        if message_ids_to_mark_read:
             try:
                  service.users().messages().batchModify(userId=user_id, body={'ids': message_ids_to_mark_read, 'removeLabelIds': ['UNREAD']}).execute()
                  logger.info(f"Attempted to mark {len(message_ids_to_mark_read)} emails as read.")
             except HttpError as error:
                  # Log error but don't fail the entire fetch if marking fails
                  logger.error(f"Error marking emails as read (scopes might be wrong: {GMAIL_SCOPES}): {error}")

        return email_contents

    except HttpError as error:
        logger.error(f'Gmail API call failed: {error}', exc_info=True)
        if error.resp.status == 401:
             logger.error("Gmail authentication error (401). Token might be revoked or invalid.")
        elif error.resp.status == 403:
             logger.error(f"Gmail permission error (403). Check API console and scopes: {GMAIL_SCOPES}")
        return [] # Return empty on API errors
    except Exception as e:
         logger.error(f"Unexpected error in get_project_emails: {e}", exc_info=True)
         return []
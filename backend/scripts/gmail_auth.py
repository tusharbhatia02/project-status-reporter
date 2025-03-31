# backend/gmail_auth.py
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import logging

logging.basicConfig(level=logging.INFO)

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Performs authentication and saves credentials to token.json.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            logging.info("Credentials loaded from token.json.")
        except Exception as e:
            logging.error(f"Error loading token.json: {e}. Will re-authenticate.")
            creds = None # Force re-authentication

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Credentials expired, attempting refresh...")
            try:
                creds.refresh(Request())
                logging.info("Credentials refreshed successfully.")
            except Exception as e:
                logging.error(f"Failed to refresh token: {e}. Need to re-authenticate.")
                creds = None # Force re-authentication
        else:
            logging.info("No valid credentials found or refresh failed. Starting authentication flow...")
            if not os.path.exists('credentials.json'):
                 logging.error("FATAL: credentials.json not found. Download it from Google Cloud Console.")
                 return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0) # Opens browser for auth
            logging.info("Authentication successful.")
        # Save the credentials for the next run
        try:
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
            logging.info("Credentials saved to token.json.")
        except Exception as e:
            logging.error(f"Failed to save token.json: {e}")
    else:
         logging.info("Valid credentials found.")
    return creds

if __name__ == '__main__':
    print("Running Gmail authentication setup...")
    returned_creds = authenticate_gmail()
    if returned_creds:
        print("Authentication successful. token.json should be created/updated.")
    else:
        print("Authentication failed. Check logs and ensure credentials.json is present.")
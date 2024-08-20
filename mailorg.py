import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def is_newsletter(message):
    subject = message['payload']['headers']
    body = message['snippet']
    
    newsletter_keywords = ["unsubscribe", "newsletter", "weekly", "daily", "digest"]
    
    for header in subject:
        if header['name'] == 'Subject':
            email_subject = header['value'].lower()
            if any(keyword in email_subject for keyword in newsletter_keywords):
                return True

    email_body = body.lower()
    if any(keyword in email_body for keyword in newsletter_keywords):
        return True
    
    return False

def archive_newsletters(service):
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No messages found.")
    else:
        for msg in messages:
            message = service.users().messages().get(userId='me', id=msg['id']).execute()
            
            if is_newsletter(message):
                # Move the message to 'Archive'
                service.users().messages().modify(userId='me', id=msg['id'], body={
                    'removeLabelIds': ['INBOX']
                }).execute()
                print(f"Archived: {message['snippet']}")

if __name__ == '__main__':
    service = authenticate_gmail()
    archive_newsletters(service)

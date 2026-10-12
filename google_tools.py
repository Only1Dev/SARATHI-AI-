import os
import json
import datetime
import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/calendar.events']

def get_google_service(service_name, version):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Missing credentials.json. Please download it from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build(service_name, version, credentials=creds)

def send_gmail(to_email, subject, body_text):
    """Sends an email using the Gmail API."""
    service = get_google_service('gmail', 'v1')
    if not service: return json.dumps({"error": "Google API not authenticated"})
    
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = to_email
    message['From'] = 'me'
    message['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'raw': encoded_message}

    try:
        sent_message = service.users().messages().send(userId="me", body=create_message).execute()
        return json.dumps({"status": "success", "message_id": sent_message["id"]})
    except Exception as e:
        return json.dumps({"error": str(e)})

def create_calendar_event(summary, start_time, duration_mins=30):
    """Creates a Google Calendar event. start_time should be ISO format string."""
    service = get_google_service('calendar', 'v3')
    if not service: return json.dumps({"error": "Google API not authenticated"})
    
    start = datetime.datetime.fromisoformat(start_time)
    end = start + datetime.timedelta(minutes=int(duration_mins))

    event = {
        'summary': summary,
        'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }
    
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return json.dumps({"status": "success", "event_link": event.get('htmlLink')})
    except Exception as e:
        return json.dumps({"error": str(e)})

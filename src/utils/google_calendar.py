from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to your credentials.json file
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = "src/utils/credentials.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build('calendar', 'v3', credentials=credentials)

def create_appointment(summary, description, start_time, end_time, attendees_emails):
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Karachi'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Karachi'},
        # 'attendees': [{'email': email} for email in attendees_emails],
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'email', 'minutes': 30}, {'method': 'popup', 'minutes': 10}],
        },
    }

    event = service.events().insert(calendarId='nazrida007@gmail.com', body=event).execute()
    print("Event Created:", event)
    return event.get('htmlLink')

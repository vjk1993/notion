import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from notion_client import Client
import pytz

# Setup Notion
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# Setup Google Calendar API
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_info(eval(os.environ["GOOGLE_CREDS"]))
service = build("calendar", "v3", credentials=creds)

# Get events from the last hour
now = datetime.utcnow()
past = now - timedelta(hours=1)
time_min = past.isoformat() + "Z"
time_max = now.isoformat() + "Z"

events = service.events().list(
    calendarId="primary",
    timeMin=time_min,
    timeMax=time_max,
    singleEvents=True,
    orderBy="startTime"
).execute().get("items", [])

for event in events:
    title = event.get("summary", "Untitled Event")
    start = event["start"].get("dateTime", event["start"].get("date"))
    
    # Create a new page in Notion
    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": start}}
        }
    )

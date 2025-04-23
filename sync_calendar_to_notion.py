import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from notion_client import Client
import pytz
from google.oauth2 import service_account

# Setup Notion
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# Setup Google Calendar API
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

# Helper to find existing Notion page by Google Event ID
def find_notion_event_by_id(event_id):
    response = notion.databases.query(
        database_id=database_id,
        filter={
            "property": "Google Event ID",
            "rich_text": {"equals": event_id}
        }
    )
    results = response.get("results", [])
    return results[0] if results else None

# Sync events
for event in events:
    title = event.get("summary", "Untitled Event")
    start = event["start"].get("dateTime", event["start"].get("date"))
    event_id = event["id"]

    existing = find_notion_event_by_id(event_id)

    if existing:
        props = existing["properties"]
        existing_title = props["Task"]["title"][0]["text"]["content"]
        existing_start = props["Due Date"]["date"]["start"]

        # Only update if something changed
        if title != existing_title or start != existing_start:
            notion.pages.update(
                page_id=existing["id"],
                properties={
                    "Task": {"title": [{"text": {"content": title}}]},
                    "Due Date": {"date": {"start": start}}
                }
            )
    else:
        # Create new event entry
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Task": {"title": [{"text": {"content": title}}]},
                "Due Date": {"date": {"start": start}},
                "Google Event ID": {"rich_text": [{"text": {"content": event_id}}]}
            }
        )

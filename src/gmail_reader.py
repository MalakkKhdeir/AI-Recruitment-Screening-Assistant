from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from pathlib import Path
import base64


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

ATTACHMENTS_DIR = Path("attachments")
ATTACHMENTS_DIR.mkdir(exist_ok=True)


def get_gmail_service():
    token_file = Path("token.json")

    credentials = Credentials.from_authorized_user_file(
        token_file,
        SCOPES
    )

    return build("gmail", "v1", credentials=credentials)


def get_emails(service, query):
    results = service.users().messages().list(
        userId="me",
        q=query
    ).execute()

    return results.get("messages", [])


def download_attachments(service, message_id):
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    payload = message["payload"]

    def process_parts(parts):
        for part in parts:

            filename = part.get("filename")

            if filename and (
                filename.lower().endswith(".pdf")
                or filename.lower().endswith(".docx")
            ):

                attachment_id = part["body"].get("attachmentId")

                if attachment_id:
                    attachment = service.users().messages().attachments().get(
                        userId="me",
                        messageId=message_id,
                        id=attachment_id
                    ).execute()

                    data = attachment["data"]

                    file_data = base64.urlsafe_b64decode(
                        data + "=" * (-len(data) % 4)
                    )

                    file_path = ATTACHMENTS_DIR / filename

                    file_path.write_bytes(file_data)

                    print(f"Downloaded: {filename}")

            if "parts" in part:
                process_parts(part["parts"])

    if "parts" in payload:
        process_parts(payload["parts"])


if __name__ == "__main__":

    service = get_gmail_service()

    messages = get_emails(
        service,
        "has:attachment (filename:pdf OR filename:docx)"
    )

    print(f"Found {len(messages)} email(s)")

    for message in messages:
        download_attachments(
            service,
            message["id"]
        )

    print("\nDone! Attachments saved in the attachments folder.")
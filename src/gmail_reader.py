
import base64
import json
import re
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = Path(__file__).resolve().parent.parent
ATTACHMENTS_DIR = BASE_DIR / "attachments"
PROCESSED_FILE = BASE_DIR / "processed_emails.json"

ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def get_gmail_service():
    """Authenticate with Gmail using the saved OAuth token."""
    token_file = BASE_DIR / "token.json"

    if not token_file.is_file():
        raise FileNotFoundError(
            "token.json was not found. Complete Gmail OAuth setup first."
        )

    credentials = Credentials.from_authorized_user_file(
        str(token_file),
        SCOPES,
    )

    return build("gmail", "v1", credentials=credentials)


def get_emails(service, query):
    """Retrieve all matching Gmail messages, handling pagination."""
    messages = []
    page_token = None

    while True:
        response = service.users().messages().list(
            userId="me",
            q=query,
            pageToken=page_token,
            maxResults=100,
        ).execute()

        messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return messages


def load_processed_emails():
    """Load IDs of emails successfully processed in previous runs."""
    if not PROCESSED_FILE.exists():
        return set()

    try:
        data = json.loads(PROCESSED_FILE.read_text(encoding="utf-8"))

        if not isinstance(data, list):
            raise ValueError("Expected a JSON list.")

        return set(str(item) for item in data)

    except (json.JSONDecodeError, OSError, ValueError) as error:
        raise RuntimeError(
            f"Could not read processed email history: {error}"
        ) from error


def save_processed_emails(processed_ids):
    """Persist processed email IDs."""
    PROCESSED_FILE.write_text(
        json.dumps(sorted(processed_ids), indent=2),
        encoding="utf-8",
    )


def safe_filename(filename):
    """Remove path components and unsafe filename characters."""
    filename = Path(filename).name
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    return filename.strip(" .") or "attachment"


def get_unique_path(filename, message_id):
    """Avoid overwriting existing attachments."""
    safe_name = safe_filename(filename)
    stem = Path(safe_name).stem
    suffix = Path(safe_name).suffix.lower()

    # Prefixing with the Gmail message ID distinguishes same-named
    # attachments received in different emails.
    safe_message_id = re.sub(r"[^a-zA-Z0-9_-]", "_", message_id)
    destination = ATTACHMENTS_DIR / (
        f"{safe_message_id}_{stem}{suffix}"
    )

    counter = 2

    while destination.exists():
        destination = ATTACHMENTS_DIR / (
            f"{safe_message_id}_{stem}_{counter}{suffix}"
        )
        counter += 1

    return destination


def decode_attachment(data):
    """Decode Gmail's URL-safe Base64 attachment data."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def download_attachments(service, message_id):
    """
    Download supported PDF and DOCX attachments for one email.

    Returns the number of successfully downloaded files.
    """
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()

    payload = message.get("payload", {})
    downloaded = 0

    def process_parts(parts):
        nonlocal downloaded

        for part in parts:
            filename = part.get("filename", "")
            body = part.get("body", {})
            attachment_id = body.get("attachmentId")

            if filename and Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    if attachment_id:
                        attachment = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(
                                userId="me",
                                messageId=message_id,
                                id=attachment_id,
                            )
                            .execute()
                        )

                        encoded_data = attachment.get("data")

                    else:
                        # Some message parts contain inline body data.
                        encoded_data = body.get("data")

                    if not encoded_data:
                        print(
                            f"Skipped {filename}: attachment data is missing."
                        )
                    else:
                        file_data = decode_attachment(encoded_data)

                        if not file_data:
                            print(f"Skipped {filename}: file is empty.")
                        else:
                            destination = get_unique_path(
                                filename,
                                message_id,
                            )
                            destination.write_bytes(file_data)

                            print(f"Downloaded: {destination.name}")
                            downloaded += 1

                except Exception as error:
                    print(
                        f"Failed to download {filename} "
                        f"from email {message_id}: {error}"
                    )

            nested_parts = part.get("parts", [])
            if nested_parts:
                process_parts(nested_parts)

    process_parts(payload.get("parts", []))

    return downloaded


def main():
    try:
        service = get_gmail_service()
        processed_ids = load_processed_emails()

    except Exception as error:
        print(f"Gmail setup failed: {error}")
        return

    query = "has:attachment {filename:pdf filename:docx}"

    try:
        messages = get_emails(service, query)
    except Exception as error:
        print(f"Could not retrieve Gmail messages: {error}")
        return

    print(f"Found {len(messages)} matching email(s).")

    for message in messages:
        message_id = message.get("id")

        if not message_id:
            print("Skipped a message without an ID.")
            continue

        if message_id in processed_ids:
            print(f"Already processed: {message_id}")
            continue

        try:
            downloaded = download_attachments(service, message_id)

            # Record the email only when downloading succeeded or
            # when no supported attachments were found. If a
            # download failed, retrying on the next run is safer.
            if downloaded > 0:
                processed_ids.add(message_id)
                save_processed_emails(processed_ids)
            else:
                print(
                    f"No files downloaded from {message_id}; "
                    "the email was not marked as processed."
                )

        except Exception as error:
            print(f"Failed to process email {message_id}: {error}")
            continue

    print("\nGmail attachment collection finished.")


if __name__ == "__main__":
    main()

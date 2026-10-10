from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow



SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate_gmail():
    base_dir = Path(__file__).resolve().parent.parent

    token_file = base_dir / "token.json"

   
    json_files = list(base_dir.glob("client_secret*.json"))

    if not json_files:
        raise FileNotFoundError(
            "Google OAuth client JSON file wasnt found."
        )

    credentials_file = json_files[0]

    credentials = None

   
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(
            token_file,
            SCOPES
        )

   
    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                SCOPES
            )

            credentials = flow.run_local_server(port=0)

       
        token_file.write_text(credentials.to_json())

    return credentials


if __name__ == "__main__":
    credentials = authenticate_gmail()

    print("Gmail authentication successful")
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ========== CONFIGURATION ==========
PDF_ROOT = r'D:\Research\backend\datasets\research-papers\papers'  # Your local PDF folder (Adjust!)
DRIVE_FOLDER_ID = '18Ytt565whnMa0y16TpiXD9PfMR9E2Ywj'               # Your personal Drive folder ID (Adjust!)

# Scopes for Drive API with file access only (created/opened by app)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Paths for OAuth 2.0 credentials and token cache
CLIENT_SECRETS_FILE = 'credentials.json'  # Path to your OAuth client secret JSON
TOKEN_FILE = 'token.json'                  # Where to save OAuth token cache

# ===================================


def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next runs
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    service = build('drive', 'v3', credentials=creds)
    return service


def list_pdf_files(root_folder):
    for dirpath, _, files in os.walk(root_folder):
        for filename in files:
            if filename.lower().endswith('.pdf'):
                yield os.path.join(dirpath, filename)


def upload_file(service, local_path, drive_folder_id):
    filename = os.path.basename(local_path)
    # Query if file already exists (by name) in the Drive folder to avoid duplicates
    query = f"name='{filename}' and '{drive_folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])
    if files:
        print(f"Skipping upload, already exists in Drive: {filename}")
        return files[0]['id']
    # Upload new file
    file_metadata = {'name': filename, 'parents': [drive_folder_id]}
    media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=True)
    request = service.files().create(body=file_metadata, media_body=media, fields='id')

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading {filename}: {int(status.progress() * 100)}% complete.")
    print(f"Uploaded {filename}, file ID: {response.get('id')}")
    return response.get('id')


def main():
    print(f"Authenticating and initializing Google Drive API client...")
    drive_service = get_drive_service()

    print(f"Searching for PDFs in local folder: {PDF_ROOT}")
    pdf_files = list(list_pdf_files(PDF_ROOT))
    print(f"Found {len(pdf_files)} PDF files to upload.")

    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"[{idx}/{len(pdf_files)}] Processing file: {pdf_path}")
            upload_file(drive_service, pdf_path, DRIVE_FOLDER_ID)
        except Exception as e:
            print(f"Failed to upload {pdf_path}: {e}")

    print("All files processed!")


if __name__ == '__main__':
    main()

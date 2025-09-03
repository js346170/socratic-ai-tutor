from google.oauth2 import service_account
from googleapiclient.discovery import build

# Define the required scopes (permissions you need)
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to your downloaded service account key JSON file
SERVICE_ACCOUNT_FILE = r"D:\service-account-key.json"

def main():
    # 1. Authenticate and create credentials using the service account key
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # 2. Build the Google Drive service client
    drive_service = build('drive', 'v3', credentials=credentials)

    # 3. Call the Drive API to list files IN YOUR SPECIFIC FOLDER
    print("Listing files from inside the 'SRL Research Data' folder...")
    folder_id = '1lIoXUROTzJDn9J8BNbRzJJbQmnwXscmz'  # The ID of your shared folder

    results = drive_service.files().list(
        pageSize=20,  # Increased the number of items to list
        # This query finds all files located inside the specified folder
        q=f"'{folder_id}' in parents and trashed = false",
        fields="nextPageToken, files(id, name, mimeType)"  # Added mimeType to see file type
    ).execute()

    items = results.get('files', [])

    # 4. Print the results
    if not items:
        print('No files found in the specified folder.')
    else:
        print('Files and Folders:')
        for item in items:
            # Print the item name, ID, and type (e.g., 'application/pdf', 'folder')
            print(f" - {item['name']} (ID: {item['id']}, Type: {item['mimeType']})")

if __name__ == '__main__':
    main()
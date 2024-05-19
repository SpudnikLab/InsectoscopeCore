import pickle
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request


def create_drive_service(service_account_file):
    # Membuat kredensial berbasis layanan dari file kunci JSON
    creds = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=['https://www.googleapis.com/auth/drive']
    )

    # Membuat objek service untuk Google Drive
    service = build('drive', 'v3', credentials=creds)
    return service

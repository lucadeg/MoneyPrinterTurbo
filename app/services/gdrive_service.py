import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger

GDRIVE_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "storage",
    "gdrive_config.json",
)

CREDENTIALS_FILE = os.path.join(
    os.path.dirname(__file__),
    "gdrive_credentials.json",
)

TOKEN_FILE = os.path.join(
    os.path.dirname(__file__),
    "gdrive_token.json",
)

TARGET_ACCOUNT = "mrvinxsrl@gmail.com"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def is_authenticated() -> bool:
    """Returns True ONLY if a real Google OAuth token file exists and is valid."""
    if not os.path.exists(TOKEN_FILE):
        return False
    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return creds and (creds.valid or (creds.expired and creds.refresh_token is not None))
    except Exception:
        return False


def get_gdrive_config() -> Dict[str, Any]:
    os.makedirs(os.path.dirname(GDRIVE_CONFIG_FILE), exist_ok=True)
    authenticated = is_authenticated()
    
    default_cfg = {
        "account": TARGET_ACCOUNT,
        "connected": authenticated,
        "root_folder": "MoneyPrinterTurbo_Cloud_Storage",
        "auto_sync_on_approve": False,
        "last_sync": None,
        "storage_quota_used_mb": 0.0,
        "total_quota_gb": 15,
        "_mock": False,
    }

    if not os.path.exists(GDRIVE_CONFIG_FILE):
        with open(GDRIVE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=2)
        return default_cfg

    try:
        with open(GDRIVE_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["connected"] = authenticated
        cfg["_mock"] = False
        return cfg
    except Exception:
        return default_cfg


def save_gdrive_config(cfg: Dict[str, Any]):
    os.makedirs(os.path.dirname(GDRIVE_CONFIG_FILE), exist_ok=True)
    with open(GDRIVE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_drive_service():
    """Builds and returns the real authenticated Google Drive API v3 client."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError(f"Google Drive Token non trovato ({TOKEN_FILE}). Configura le credenziali OAuth prima di procedere.")

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def authenticate_gdrive() -> Dict[str, Any]:
    """Runs local OAuth2 InstalledAppFlow using gdrive_credentials.json."""
    if not os.path.exists(CREDENTIALS_FILE):
        return {
            "success": False,
            "error": f"File credenziali non trovato: {CREDENTIALS_FILE}. Scarica credentials.json da Google Cloud Console.",
        }

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())

        cfg = get_gdrive_config()
        cfg["connected"] = True
        cfg["last_sync"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_gdrive_config(cfg)

        return {"success": True, "account": TARGET_ACCOUNT}
    except Exception as e:
        logger.error(f"Google Drive OAuth authentication failed: {e}")
        return {"success": False, "error": str(e)}


def upload_video_to_gdrive(file_path: str, title: str, channel_name: str = "Generale") -> Dict[str, Any]:
    """Uploads a video to Google Drive via real Google Drive v3 API with resumable upload."""
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File non trovato: {file_path}"}

    if not is_authenticated():
        return {
            "success": False,
            "error": "Google Drive non autenticato. Completa l'autenticazione OAuth nella scheda Google Drive prima di caricare.",
        }

    try:
        from googleapiclient.http import MediaFileUpload

        service = get_drive_service()
        file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

        # 1. Search or create root folder
        cfg = get_gdrive_config()
        root_folder_name = cfg.get("root_folder", "MoneyPrinterTurbo_Cloud_Storage")
        
        folder_query = f"name = '{root_folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=folder_query, spaces='drive', fields='files(id, name)').execute()
        folders = results.get('files', [])
        
        if not folders:
            folder_metadata = {
                'name': root_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            root_folder = service.files().create(body=folder_metadata, fields='id').execute()
            root_folder_id = root_folder.get('id')
        else:
            root_folder_id = folders[0].get('id')

        # 2. Upload file
        file_metadata = {
            'name': f"{title}.mp4",
            'parents': [root_folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
        uploaded = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        file_id = uploaded.get('id')
        link = uploaded.get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view")

        # 3. Update stats
        cfg["storage_quota_used_mb"] = round(cfg.get("storage_quota_used_mb", 0) + file_size_mb, 2)
        cfg["last_sync"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_gdrive_config(cfg)

        return {
            "success": True,
            "file_id": file_id,
            "link": link,
            "folder": root_folder_name,
            "account": TARGET_ACCOUNT,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size_mb": file_size_mb,
        }
    except Exception as e:
        logger.error(f"Google Drive upload error: {e}")
        return {"success": False, "error": str(e)}


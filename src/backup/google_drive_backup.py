"""
Google Drive Backup Module
Exports PostgreSQL tables to CSV and uploads to Google Drive
"""
import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..utils.db import db
from ..utils.logger import logger
from ..utils.config import config

SCOPES = ['https://www.googleapis.com/auth/drive.file']

TABLES_TO_BACKUP = [
    "signals",
    "normalized_prices",
    "normalized_leverage", 
    "normalized_sentiment",
    "normalized_macro",
    "normalized_cycle"
]

class GoogleDriveBackup:
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.folder_id = os.getenv("DRIVE_FOLDER_ID")
        self.service = None
        if self.credentials_path and os.path.exists(self.credentials_path):
            self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive authenticated successfully")
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            self.service = None

    def export_table_to_csv(self, table_name: str, output_dir: str = "/home/ubuntu/crash_radar/backups") -> Optional[str]:
        """Export a PostgreSQL table to CSV"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{table_name}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        try:
            rows = db.execute(f"SELECT * FROM {table_name}")
            
            if not rows:
                logger.warning(f"No data in {table_name}, skipping export")
                return None
            
            with open(filepath, 'w', newline='') as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            
            logger.info(f"Exported {table_name} to {filepath} ({len(rows)} rows)")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting {table_name}: {e}")
            return None

    def upload_to_drive(self, filepath: str, folder_id: Optional[str] = None) -> Optional[str]:
        """Upload a file to Google Drive"""
        if not self.service:
            logger.warning("Google Drive not authenticated, skipping upload")
            return None
        
        folder_id = folder_id or self.folder_id
        
        try:
            file_metadata = {
                'name': os.path.basename(filepath),
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaFileUpload(filepath, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            logger.info(f"Uploaded {filepath} to Google Drive: {file.get('webViewLink')}")
            return file.get('webViewLink')
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return None

    def backup_all_tables(self, upload: bool = True) -> dict:
        """Backup all tables to CSV and optionally upload to Google Drive"""
        results = {
            "exported": [],
            "uploaded": [],
            "errors": []
        }
        
        db.initialize()
        
        for table in TABLES_TO_BACKUP:
            try:
                filepath = self.export_table_to_csv(table)
                if filepath:
                    results["exported"].append(filepath)
                    
                    if upload:
                        link = self.upload_to_drive(filepath)
                        if link:
                            results["uploaded"].append({"file": filepath, "link": link})
            except Exception as e:
                results["errors"].append({"table": table, "error": str(e)})
        
        db.close()
        
        logger.info(f"Backup complete: {len(results['exported'])} exported, {len(results['uploaded'])} uploaded")
        return results

    def create_backup_manifest(self, results: dict) -> str:
        """Create a manifest JSON file with backup details"""
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "tables": TABLES_TO_BACKUP,
            "exported_files": results.get("exported", []),
            "uploaded_files": results.get("uploaded", [])
        }
        
        manifest_path = "/home/ubuntu/crash_radar/backups/manifest.json"
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path


def run_weekly_backup():
    """Run weekly backup (called by cron)"""
    logger.info("Starting weekly Google Drive backup")
    backup = GoogleDriveBackup()
    results = backup.backup_all_tables(upload=True)
    
    if results["exported"]:
        backup.create_backup_manifest(results)
    
    return results


if __name__ == "__main__":
    run_weekly_backup()

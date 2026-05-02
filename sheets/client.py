#sheets/client.py
# Manage the single connection to google sheet
# Uses the singelton pattern via lru_cache to avoid
# reconnecting on every request

import gspread
from google.oauth2.service_account import Credentials
from functools import lru_cache
import os

# The scopes define exactly what permissions we're requesting
# We only ask for what we need — principle of least privilege

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

@lru_cache(maxsize=1)
def get_spreadsheet():
    """
    Returns the main QualityIQ spreedsheet

    This function runs once and cache the result.
    Every subsequent call returns the cached spreadsheet object
    without reconnecting to Google.

    Returns:
    gspread.Spreadsheet object
    """
    credentials_file = os.getenv(
        "GOOGLE_CREDENTIALs_FILE",
        "credentials.json"
    )

    creds = Credentials.from_service_account_file(
        credentials_file,
        scopes = SCOPES
    )

    client = gspread.authorize(creds)

    sheet_id = os.getenv("SHEET_ID")

    if not sheet_id:
        raise ValueError(
            "SHEET_ID not found in environment variables."
            "Check your .env file."
        )
    return client.open_by_key(sheet_id)

def get_sheet(name: str):
    """
    Returns a specific worksheet by name.

    Args:
        name: the tab name in Google sheets

    Returns:
        gspread.worksheet object

    Raises:
        gspread.exceptions.WorksheetNotFound if the tab doesn't exist

    """
    return get_spreadsheet().worksheet(name)

def clear_connection_cache():
    """
    Forces a fresh connection on the next request
    Call this if the spreadsheet connection becomes stale

    """
    get_spreadsheet.cache_clear()
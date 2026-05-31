
"""
Chạy script này MỘT LẦN để tạo cấu trúc Google Sheets.
Sau đó không cần chạy nữa.

Cách dùng:
    GEMINI_API_KEY=... GROQ_API_KEY=... GOOGLE_CREDS_JSON='...' SHEET_ID=... python src/setup_sheets.py
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials

GOOGLE_CREDS = json.loads(os.environ["GOOGLE_CREDS_JSON"])
SHEET_ID     = os.environ["SHEET_ID"]

def setup():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_info(GOOGLE_CREDS, scopes=scopes)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SHEET_ID)

    # ── Sheet 1: TruyenDai
    try:
        ws = sheet.worksheet("TruyenDai")
        print("Sheet TruyenDai đã tồn tại")
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet("TruyenDai", rows=1000, cols=10)
        print("Đã tạo sheet TruyenDai")
    ws.clear()
    ws.append_row(["story_id", "story_title", "chapter_num", "chapter_title", "content", "created_at", "status"])
    ws.format("A1:G1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}})

    # ── Sheet 2: TruyenNgan
    try:
        ws2 = sheet.worksheet("TruyenNgan")
        print("Sheet TruyenNgan đã tồn tại")
    except gspread.WorksheetNotFound:
        ws2 = sheet.add_worksheet("TruyenNgan", rows=500, cols=10)
        print("Đã tạo sheet TruyenNgan")
    ws2.clear()
    ws2.append_row(["story_id", "story_title", "chapter_num", "chapter_title", "content", "created_at", "status"])
    ws2.format("A1:G1", {"textFormat": {"bold": True}})

    # ── Sheet 3: Config
    try:
        ws3 = sheet.worksheet("Config")
        print("Sheet Config đã tồn tại")
    except gspread.WorksheetNotFound:
        ws3 = sheet.add_worksheet("Config", rows=100, cols=5)
        print("Đã tạo sheet Config")
    ws3.clear()
    ws3.append_row(["key", "value", "updated_at"])
    ws3.append_row(["current_story_idx", "0", ""])
    ws3.append_row(["chapter_long_1", "0", ""])
    ws3.append_row(["chapter_long_2", "0", ""])
    ws3.append_row(["used_themes", "", ""])
    ws3.format("A1:C1", {"textFormat": {"bold": True}})

    print("\n✅ Setup hoàn tất!")
    print(f"📋 Mở Google Sheets: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

if __name__ == "__main__":
    setup()

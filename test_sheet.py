import os
import json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("--- BẮT ĐẦU KIỂM TRA KẾT NỐI GOOGLE SHEET ---")

try:
    # 1. Giải mã credentials
    creds_b64 = os.environ.get("GOOGLE_CREDS_BASE64")
    if not creds_b64:
        raise ValueError("LỖI: Chưa cấu hình biến GOOGLE_CREDS_BASE64 trong GitHub Secrets!")
        
    creds_json = json.loads(base64.b64decode(creds_b64).decode('utf-8'))
    print("✅ Giải mã tài khoản dịch vụ thành công.")

    # 2. Kết nối API
    scope = ["https://google.com", "https://googleapis.com"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    print("✅ Kết nối đến máy chủ Google API thành công.")

    # 3. Mở file và đọc thử
    sheet = client.open("Bot_Truyen_Kinh_Di")
    ws_cau_hinh = sheet.worksheet("CauHinh")
    
    ten_truyen = ws_cau_hinh.acell('B2').value
    tap_hien_tai = ws_cau_hinh.acell('D2').value
    
    print(f"✅ ĐÃ THÔNG VỚI GOOGLE SHEET!")
    print(f"   👉 Tên truyện đọc được: {ten_truyen}")
    print(f"   👉 Tập hiện tại đọc được: {tap_hien_tai}")
    print("--- KIỂM TRA HOÀN TẤT: KHÔNG CÓ LỖI ---")

except gspread.exceptions.SpreadsheetNotFound:
    print("❌ LỖI: Không tìm thấy file nào tên là 'Bot_Truyen_Kinh_Di' trên Drive.")
    print("   👉 Hãy kiểm tra lại xem bạn đã đổi tên file giống hệt chưa (chú ý viết hoa, viết thường, gạch dưới).")
except gspread.exceptions.APIError as e:
    print(f"❌ LỖI PHÂN QUYỀN: Google từ chối truy cập! Chi tiết: {e}")
    print("   👉 Hãy chắc chắn bạn đã bấm nút 'Chia sẻ' trên Sheet và thêm email tài khoản dịch vụ làm 'Người chỉnh sửa'.")
except Exception as e:
    print(f"❌ LỖI KHÁC: {e}")

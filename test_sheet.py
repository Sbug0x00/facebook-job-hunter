import os
import json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("--- BẮT ĐẦU KIỂM TRA KẾT NỐI VỚI GOOGLE SHEET CỦA BẠN ---")

try:
    # 1. Lấy chuỗi Base64 từ GitHub Secrets
    creds_b64 = os.environ.get("GOOGLE_CREDS_BASE64")
    if not creds_b64:
        raise ValueError("LỖI: Chưa cấu hình biến GOOGLE_CREDS_BASE64 trong GitHub Secrets!")
    
    # TỰ ĐỘNG SỬA LỖI INCORRECT PADDING: Thêm các dấu '=' vào cuối nếu chuỗi bị thiếu
    creds_b64 = creds_b64.strip()
    missing_padding = len(creds_b64) % 4
    if missing_padding:
        creds_b64 += '=' * (4 - missing_padding)
        print("🔧 Hệ thống đã tự động vá lỗi đệm ký tự (Incorrect Padding).")

    # 2. Giải mã cấu trúc JSON
    creds_json = json.loads(base64.b64decode(creds_b64).decode('utf-8'))
    print("✅ Giải mã tài khoản dịch vụ thành công.")

    # 3. Kết nối đến Google API
    scope = ["https://google.com", "https://googleapis.com"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    print("✅ Kết nối đến máy chủ Google API thành công.")

    # 4. Định vị trực tiếp bằng ID file Google Sheet bạn cung cấp
    FILE_ID = "1u0jpBr0cWZQhtVyIUep08TmkGILK0j3qpRYdHWPfRCU"
    sheet = client.open_by_key(FILE_ID)
    print(f"✅ Đã tìm thấy chính xác file Google Sheet trên Drive của bạn.")

    # 5. Tự động kiểm tra và khởi tạo các thẻ (Tab) nếu Sheet đang trắng trơn
    try:
        ws_cau_hinh = sheet.worksheet("CauHinh")
    except gspread.exceptions.WorksheetNotFound:
        # Nếu chưa có thẻ CauHinh, bot tự tạo luôn thay vì báo lỗi
        ws_cau_hinh = sheet.add_worksheet(title="CauHinh", rows="100", cols="20")
        print("🆕 Đã tự động tạo thẻ 'CauHinh' do file của bạn đang trống.")
        
    try:
        ws_kho_truyen = sheet.worksheet("KhoTruyen")
    except gspread.exceptions.WorksheetNotFound:
        # Nếu chưa có thẻ KhoTruyen, bot tự tạo luôn
        ws_kho_truyen = sheet.add_worksheet(title="KhoTruyen", rows="1000", cols="20")
        print("🆕 Đã tự động tạo thẻ 'KhoTruyen' để lưu lịch sử.")

    # 6. Kiểm tra xem đã điền dữ liệu mẫu chưa, nếu chưa thì tự điền luôn!
    if not ws_cau_hinh.acell('A1').value:
        print("📝 Đang tự động nạp cấu hình mẫu ban đầu vào file Sheet của bạn...")
        # Điền hàng tiêu đề
        ws_cau_hinh.update('A1:E1', [['Cookie_Facebook', 'Ten_Truyen', 'Cot_Truyen', 'Tap_Hien_Tai', 'Tong_So_Tap']])
        # Điền hàng dữ liệu mẫu
        ws_cau_hinh.update('A2:E2', [[
            'SỬ DỤNG COOKIE TRÊN GOOGLE SHEET', 
            'Mật Mã Bí Ẩn Của Hội Tam Điểm', 
            'Một học sinh tại trường phép thuật vô tình giải mã được bức thư cổ của giáo sư bị mất tích, dẫn lối tới mật thất chứa linh hồn hắc ám...', 
            '1', 
            '5'
        ]])
        
        # Điền tiêu đề cho kho truyện
        ws_kho_truyen.update('A1:D1', [['Tiêu đề bài viết', 'Nội dung truyện do AI viết', 'Trạng thái đăng', 'Thời gian đăng']])
        print("✅ Đã ghi thành công dữ liệu mẫu vào Google Sheet!")
    else:
        print(f"👉 Tên truyện hiện tại trong file: {ws_cau_hinh.acell('B2').value}")
        print(f"👉 Tập hiện tại: {ws_cau_hinh.acell('D2').value}")

    print("--- KIỂM TRA HOÀN TẤT: HỆ THỐNG ĐÃ THÔNG THOÁNG 100% ---")

except json.decoder.JSONDecodeError:
    print("❌ LỖI NGHIÊM TRỌNG: Chuỗi Base64 giải mã ra nội dung không đúng định dạng JSON.")
    print("   👉 Bạn hãy vào trang base64encode.org làm lại, copy chuẩn file gốc .json và dán lại vào GitHub Secrets nhé.")
except Exception as e:
    print(f"❌ LỖI HỆ THỐNG: {e}")
    print("❌ LỖI: Không tìm thấy file nào tên là 'Bot_Truyen_Kinh_Di' trên Drive.")
    print("   👉 Hãy kiểm tra lại xem bạn đã đổi tên file giống hệt chưa (chú ý viết hoa, viết thường, gạch dưới).")
except gspread.exceptions.APIError as e:
    print(f"❌ LỖI PHÂN QUYỀN: Google từ chối truy cập! Chi tiết: {e}")
    print("   👉 Hãy chắc chắn bạn đã bấm nút 'Chia sẻ' trên Sheet và thêm email tài khoản dịch vụ làm 'Người chỉnh sửa'.")
except Exception as e:
    print(f"❌ LỖI KHÁC: {e}")

import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("--- BẮT ĐẦU KIỂM TRA KẾT NỐI THEO PHƯƠNG PHÁP TEXT THUỒN ---")

try:
    # 1. Đọc trực tiếp chữ thường từ GitHub Secrets, bỏ qua Base64 phức tạp
    client_email = os.environ.get("GOOGLE_CLIENT_EMAIL")
    private_key = os.environ.get("GOOGLE_PRIVATE_KEY")
    
    if not client_email or not private_key:
        raise ValueError("LỖI: Chưa cấu hình biến GOOGLE_CLIENT_EMAIL hoặc GOOGLE_PRIVATE_KEY trên GitHub!")

    # Tự động dọn dẹp và xử lý ký tự xuống dòng ẩn (\n) trong chuỗi Private Key
    private_key = private_key.replace('\\n', '\n').strip()

    # 2. Đóng gói thủ công cấu trúc Service Account chuẩn 100% cho thư viện gspread
    creds_dict = {
        "type": "service_account",
        "client_email": client_email,
        "private_key": private_key,
        "token_uri": "https://googleapis.com",
    }
    print("✅ Đóng gói tài khoản dịch vụ dạng Chữ thuần thành công.")

    # 3. Kết nối API
    scope = ["https://google.com", "https://googleapis.com"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    print("✅ Kết nối đến máy chủ Google API thành công.")

    # 4. Định vị trực tiếp bằng ID file Google Sheet của bạn
    FILE_ID = "1u0jpBr0cWZQhtVyIUep08TmkGILK0j3qpRYdHWPfRCU"
    sheet = client.open_by_key(FILE_ID)
    print(f"✅ Đã tìm thấy chính xác file Google Sheet trên Drive của bạn.")

    # 5. Tự động kiểm tra và khởi tạo các thẻ (Tab) nếu Sheet đang trắng trơn
    try:
        ws_cau_hinh = sheet.worksheet("CauHinh")
    except gspread.exceptions.WorksheetNotFound:
        ws_cau_hinh = sheet.add_worksheet(title="CauHinh", rows="100", cols="20")
        print("🆕 Đã tự động tạo thẻ 'CauHinh' thành công.")
        
    try:
        ws_kho_truyen = sheet.worksheet("KhoTruyen")
    except gspread.exceptions.WorksheetNotFound:
        ws_kho_truyen = sheet.add_worksheet(title="KhoTruyen", rows="1000", cols="20")
        print("🆕 Đã tự động tạo thẻ 'KhoTruyen' thành công.")

    # 6. Tự động viết dữ liệu mẫu ban đầu
    if not ws_cau_hinh.acell('A1').value:
        print("📝 Đang tự động nạp cấu hình mẫu ban đầu vào file Sheet của bạn...")
        ws_cau_hinh.update('A1:E1', [['Cookie_Facebook', 'Ten_Truyen', 'Cot_Truyen', 'Tap_Hien_Tai', 'Tong_So_Tap']])
        ws_cau_hinh.update('A2:E2', [[
            'SỬ DỤNG COOKIE TRÊN GOOGLE SHEET', 
            'Mật Mã Bí Ẩn Của Hội Tam Điểm', 
            'Một học sinh tại trường phép thuật vô tình giải mã được bức thư cổ của giáo sư bị mất tích, dẫn lối tới mật thất chứa linh hồn hắc ám...', 
            '1', 
            '5'
        ]])
        ws_kho_truyen.update('A1:D1', [['Tiêu đề bài viết', 'Nội dung truyện do AI viết', 'Trạng thái đăng', 'Thời gian đăng']])
        print("✅ Đã ghi thành công dữ liệu mẫu vào Google Sheet của bạn!")
    else:
        print(f"👉 Tên truyện đang có sẵn trong file: {ws_cau_hinh.acell('B2').value}")
        print(f"👉 Tập hiện tại: {ws_cau_hinh.acell('D2').value}")

    print("--- KIỂM TRA HOÀN TẤT: HỆ THỐNG ĐÃ THÔNG THOÁNG 100% ---")

except Exception as e:
    print(f"❌ LỖI HỆ THỐNG: {e}")

import os
import json
import time
import random
import base64
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import g4f
from playwright.sync_api import sync_playwright

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & KẾT NỐI GOOGLE SHEET
# ==========================================
def ket_noi_google_sheet():
    # Giải mã tài khoản dịch vụ Google từ chuỗi Base64 trong GitHub Secrets
    creds_b64 = os.environ.get("GOOGLE_CREDS_BASE64")
    creds_json = json.loads(base64.b64decode(creds_b64).decode('utf-8'))
    
    scope = ["https://google.com", "https://googleapis.com"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    
    # Mở Google Sheet bằng Tên file (Đảm bảo đã share quyền chỉnh sửa cho email tài khoản dịch vụ)
    sheet = client.open("Bot_Truyen_Kinh_Di")
    return sheet.worksheet("CauHinh"), sheet.worksheet("KhoTruyen")

# ==========================================
# 2. XỬ LÝ SÁNG TÁC ĐA TẦNG (GEMINI + G4F)
# ==========================================
def don_dep_vong_chu(text):
    # Hàm loại bỏ các ký tự định dạng Markdown thừa thãi để text sạch khi lên Facebook
    bad_chars = ["**", "*", "__", "###", "##"]
    for char in bad_chars:
        text = text.replace(char, "")
    return text.strip()

def sang_tac_truyen(ten_truyen, tap_hien_tai, cot_truyen):
    # Tầng 1: Dùng Gemini API phác thảo nội dung
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
    
    prompt_gemini = f"""
    Hãy viết tiếp Tập {tap_hien_tai} của bộ truyện kinh dị dài tập có tên '{ten_truyen}'.
    Cốt truyện tổng thể: {cot_truyen}.
    Yêu cầu: Nội dung chứa các yếu tố ma thuật hắc ám và biểu tượng học huyền bí. 
    Kết thúc tập này phải dừng lại ở một tình huống cực kỳ gay cấn, lửng lơ để kích thích người đọc xem tiếp tập sau.
    Viết khoảng 600 chữ bằng tiếng Việt.
    """
    
    try:
        response = model.generate_content(prompt_gemini)
        ban_thao = response.text
    except Exception as e:
        print(f"Lỗi gọi Gemini, chuyển sang dùng kho truyện dự phòng: {e}")
        ban_thao = f"Cơn ác mộng tại tu viện cổ lại tiếp diễn ở Tập {tap_hien_tai}. Những ký tự Latin trên tường bắt đầu rỉ máu..."

    # Tầng 2: Dùng G4F (AI miễn phí không tài khoản) chuốt lại văn phong phong cách Harry Potter + Dan Brown
    prompt_g4f = f"""
    Hãy biên tập lại đoạn văn bản sau đây thành một chương truyện kinh dị. 
    Sử dụng văn phong kết hợp giữa sự huyền bí, trường học phù thủy của Harry Potter và tính trinh thám, giải mã mật mã, hội kín của Dan Brown.
    Làm cho câu chữ trở nên u ám, nghẹt thở và sâu sắc hơn. Giữ nguyên cốt truyện gốc.
    
    Văn bản gốc:
    {ban_thao}
    """
    
    try:
        # Thử gọi DuckDuckGo qua G4F, nếu lỗi tự động đổi sang các Provider dự phòng khác trong thư viện
        truyen_hay = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt_g4f}],
            provider=g4f.Provider.DuckDuckGo
        )
    except Exception:
        try:
            truyen_hay = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": prompt_g4f}],
                provider=g4f.Provider.Liaobots
            )
        except Exception:
            truyen_hay = ban_thao # Nếu tất cả AI tầng 2 lỗi, giữ nguyên bản thảo tầng 1

    return don_dep_vong_chu(truyen_hay)

# ==========================================
# 3. TẠO ẢNH AI CHUẨN KÍCH THƯỚC FACEBOOK
# ==========================================
def tao_va_tai_anh(ten_truyen):
    # Dịch tên truyện hoặc tạo prompt tiếng Anh cơ bản cho ảnh
    prompt_anh = f"gothic horror scene, mystery symbols, ancient magic school, cinematic lighting, dark background, related to {ten_truyen}"
    prompt_encoded = requests.utils.quote(prompt_anh)
    
    # Ép kích thước ảnh chữ nhật chuẩn Facebook (1200x630) vào URL Pollinations.ai
    url_anh = f"https://pollinations.ai{prompt_encoded}?width=1200&height=630&nologo=true"
    
    file_path = "/tmp/illustration.jpg"
    response = requests.get(url_anh)
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path

# ==========================================
# 4. TRÌNH DUYỆT NGẦM ĐĂNG FACEBOOK QUA COOKIE
# ==========================================
def dang_bai_facebook(tieu_de, noi_dung, file_anh, cookie_str):
    cookies = json.loads(cookie_str)
    
    with sync_playwright() as p:
        # Chạy ẩn danh hoàn toàn (headless=True), giả lập thiết bị thật bằng User-Agent
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_cookies(cookies)
        
        page = context.new_page()
        # Sử dụng giao diện mbasic của Facebook để tối ưu hóa tốc độ cào và né checkpoint
        page.goto("https://facebook.com")
        
        # Kiểm tra xem cookie còn sống không
        if "Bạn đang nghĩ gì" not in page.content() and "composer" not in page.content():
            print("Cookie Facebook đã hết hạn hoặc bị lỗi!")
            browser.close()
            return False
            
        # Điều hướng vào ô đăng bài kèm ảnh
        page.click("input[name='view_photo']")
        time.sleep(random.randint(3, 6)) # Trễ ngẫu nhiên né quét spam
        
        # Nhập văn bản hoàn chỉnh
        van_ban_post = f"{tieu_de}\n\n{noi_dung}\n\n#truyenkinhdi #huyenbi #danbrown #harrypotter"
        page.fill("textarea[name='xc_message']", van_ban_post)
        
        # Tải ảnh lên
        page.set_input_files("input[type='file']", file_path=file_path)
        time.sleep(random.randint(4, 7))
        
        # Bấm nút Xem trước / Đăng bài
        page.click("input[name='view_overview']")
        time.sleep(random.randint(3, 5))
        page.click("input[name='submit']")
        time.sleep(5)
        
        # Thu thập lại Cookie mới (nếu Facebook có cập nhật phiên) để lưu đè lại
        new_cookies = context.cookies()
        browser.close()
        return json.dumps(new_cookies)

# ==========================================
# 5. ĐIỀU KHIỂN LUỒNG VÀ CHẠY CHÍNH (MAIN)
# ==========================================
def main():
    try:
        ws_cau_hinh, ws_kho_truyen = ket_noi_google_sheet()
        
        # Đọc dữ liệu cấu hình từ Tab CauHinh
        cookie_fb = ws_cau_hinh.acell('A2').value
        ten_truyen = ws_cau_hinh.acell('B2').value
        cot_truyen = ws_cau_hinh.acell('C2').value
        tap_hien_tai = int(ws_cau_hinh.acell('D2').value)
        tong_so_tap = int(ws_cau_hinh.acell('E2').value)
        
        print(f"Bắt đầu xử lý: {ten_truyen} - Tập {tap_hien_tai}/{tong_so_tap}")
        
        # Kiểm tra xem truyện đã kết thúc chưa
        if tap_hien_tai > tong_so_tap:
            print("Bộ truyện hiện tại đã hoàn thành tất cả các tập. Vui lòng cập nhật bộ truyện mới trên Google Sheet.")
            return

        # Bước 1: Gọi hệ thống AI viết bài
        tieu_de_bai_viet = f"[Tập {tap_hien_tai}/{tong_so_tap}] - {ten_truyen.upper()}"
        noi_dung_truyen = sang_tac_truyen(ten_truyen, tap_hien_tai, cot_truyen)
        
        # Bước 2: Tạo ảnh minh họa độc quyền
        file_anh = tao_va_tai_anh(ten_truyen)
        
        # Bước 3: Đăng bài lên Facebook bằng Trình duyệt ngầm
        cookie_cap_nhat = dang_bai_facebook(tieu_de_bai_viet, noi_dung_truyen, file_anh, cookie_fb)
        
        if cookie_cap_nhat:
            print("Đăng bài lên Facebook thành công!")
            
            # Ghi lịch sử bài đăng vào Tab KhoTruyen làm bản lưu trữ cho bạn duyệt/xem lại
            ws_kho_truyen.append_row([tieu_de_bai_viet, noi_dung_truyen, "Thành công", time.strftime("%Y-%m-%d %H:%M:%S")])
            
            # Bước 4: Tăng số tập lên 1 cho ngày mai và lưu lại Cookie mới nhất vào Google Sheet
            ws_cau_hinh.update_acell('D2', str(tap_hien_tai + 1))
            ws_cau_hinh.update_acell('A2', cookie_cap_nhat)
            print("Đã cập nhật trạng thái mới lên Google Sheets.")
        else:
            print("Đăng bài thất bại do lỗi duyệt web.")
            
        # Xóa file ảnh tạm để không làm đầy bộ nhớ máy ảo GitHub
        if os.path.exists(file_anh):
            os.remove(file_anh)
            
    except Exception as e:
        print(f"Hệ thống gặp lỗi nghiêm trọng: {e}")

if __name__ == "__main__":
    main()

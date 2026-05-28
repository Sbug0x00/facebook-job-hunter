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
    creds_b64 = os.environ.get("ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAic291bmQtbWFudHJhLTQ5NzcwNy1pOSIsCiAgInByaXZhdGVfa2V5X2lkIjogImU1MWJjZjNjZDE3NzgxOTY1ZmFjM2RjYmI0MGRkYWNlNmZjZWUwOTMiLAogICJwcml2YXRlX2tleSI6ICItLS0tLUJFR0lOIFBSSVZBVEUgS0VZLS0tLS1cbk1JSUV2Z0lCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktnd2dnU2tBZ0VBQW9JQkFRQ203L1RKaUlVWTB1aVVcbjZGVEY4TmRSRVd5cWRBTHF2aVdRTUpmM3V3ajdWb1hsbng1Z3VGT2ZyUnoxdDNINmt5M21pWFEydXVkQWxiRGpcbiszMkFURmNmNDlITUlvZG1VeHVrQjR4ZUk2K0FOTFJvbU1sWDlBZnM1Zmp5YUxGWDFNaWZnUmxyZVdWOElZOXBcbjlRSGJZR1M4T1haTlkrV2tIS3h2MWpwMEpvbktEQUhMcHdRRThsWkhnZTRzVHNoM2tjZm54WnhwRVM4SDJBRE1cblVOSFpOM3hOUDdVaUU1Z0FUZXhZZFJIVGc2ZzRnUk5SbFJFVk9uNFh2U29ISVlHRUU4VklRY3REc1dkN3JxMVFcbkYxY2dwb3lTY1o0WWI1MkNIaE9aMDMxV0VBSEo3T0NlU0hENUNMNjNHb25uM3puQm55b0hrMy94UjdlVmpYS0RcbjVvL1IvS2RGQWdNQkFBRUNnZ0VBRXkxQWdRQTZUZW80aHBhVDJuTTZ3TmpRRTFxbFZTTUh2S01nYWZobDVUMkFcbnZ5cUN1bGlpWHBicjJ6dzZEeTltRi9RVlVnNHhiNFZpbnlYdU9sVktzdUtnWUtOY3kzL2pqbm5CZ2JUMnZiTVFcblFHM0F2MlpNbk1Xa1RmQ0I0dFdTUUdSN3I1RnYrNHo5WlE0Y3F2OU5ReVFVdDNvdzBLUHNtU0pTYjdKWHBNcUJcbjBRYVkvaFNwenFFV2NjOVJZUWRmSUZzK0JRWDhCaGhsVWVxYjNxaTBZTEF2bGs0c3BxOTVhODhmR1N1R1FXWC9cbnJkSVQrQUdBSm96Vkc2SEtWSFN1VGVNUlVBTE9RK2lEcThxQVdnUVBjUDFxY2ZEMGRqQlk0MTZ5S3dZRE5jOTdcbjJyZFlWRTJ4QklYVnV6Vm5xTXVHbHdnemxwZ2tiN3dsLzdWSndNVWY1d0tCZ1FEUVNmZlRRcVBWeFdUNkp6NFRcbnZ6bjQ5UVZycjlYZkdGQ0FqTGZFNHJSVVpLOFhTQUZHTnYvUDcxemp1dnVRVjVWZjJBQ21TUnZ0SC9hMjZyNGpcblgwdnlaNXVSTi9DOUViTWUwWXAzOStLSHI4V21UOFFGeFZqK1QxaGVGVUxXU1ZPZ0dabTcvY1JLbTU5MTUyVEJcbitGS0E5elEyRnlrSnR3MzM2QStDQVJiSTN3S0JnUUROTFNMU0l2RG8wcXdrWERFZldGLzJ6M0VpalVPa1ExNkRcbkN3d0NRbkRrK1psTG1KOHFmOVcvOFpYbGZMUWRPRWtmNyt3ZTl4NWZ1bXBUdmtrRUR2TVZ5NXJwNE9kRW1UQVhcbkhNeXhUZG1sckJVL01vZEw3L1BhYkNSa3JweVI4aDFpN0hUTDROUVgwQmxCczdGRklXRjk2U2ZTM0k5dmo0MzBcbjdTc0xvMFRBV3dLQmdRQ3NxdlVJTERGWFVMbEI2dkE2UElkWmkvMS9aUmZlUnZETmNGb1RuSUF6aWZmZ1MrL0tcbmZtT1l3K3gwV1JpY2N3N0FrbmNQWW9JRkZEOVpLY2FQMmp0Q2E0TjZZaTV1L2xKSUZScytFciszRGc3Q3JWTnFcbkdVeUtIY3E2eTlOSmd5WVJEY2YxSVF6dGNJOURsWnhnZEhRb3QwV1FKYWoraGNMTnBaSGRpdnVSYndLQmdCV3FcbjQ1ZC9leU9MUkFTZSs4ME1ueTNJWUhFK3E5c0lCazRlZDRreGpReVJVMkFKWVIyeTNGYmw0MmVWME11Wkt4ZkZcblZaRTdsYWlVWGpBejB6QXJoLzVRUHk3ZHdtNmJJdG45LzV2bDFjdEtMZ0E3ak5BM0tmQnlKVEhBd3VZaXhIbXlcbjhPNnE4cHNGTGZXalRXQTRrendoeUVQYmFRWm1DWjdKQVJlOGlVRXJBb0dCQUx6bDdCVjhrVVVwNTZBaE9ueTFcblNsOTdOWkNIQ25zbjZtZXdaZGJYMVNEdjQ5d0Z5MkxGYUMveFp6cFJMS1E3cDV1c3ExMjdIUUxXS0gwTjJ4YVBcbmhmdncwRnM0eTlrOEtqaTMyNE5VL0RmL3VyYVFjU2ZzQjNJWUhlWDdrSVg2OXVyeDNVRGZnMjBuajRxN1R5Rm1cbjVPSU1FUTI3ZFF0U29BWTg3MEdSd3lOSVxuLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLVxuIiwKICAiY2xpZW50X2VtYWlsIjogImZiLWJvdC10cnV5ZW5Ac291bmQtbWFudHJhLTQ5NzcwNy1pOS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMTMyODE2NzE4NTYwMTQzNDE1MDgiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ZiLWJvdC10cnV5ZW4lNDBzb3VuZC1tYW50cmEtNDk3NzA3LWk5LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIgp9Cg")
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

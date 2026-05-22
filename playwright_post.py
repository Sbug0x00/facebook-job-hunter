#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import time
import os
from playwright.async_api import async_playwright
from datetime import datetime

# Load config
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Load nội dung bài viết từ file
with open('post_content.json', 'r', encoding='utf-8') as f:
    post_data = json.load(f)

async def post_to_facebook(email, password, page_url):
    """
    Đăng nhập Facebook và post bài lên Page
    """
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("🔐 Đang đăng nhập Facebook...")
            
            # Bước 1: Đăng nhập Facebook
            await page.goto("https://www.facebook.com/login")
            await page.wait_for_load_state("networkidle")
            
            # Điền email
            await page.fill('input[name="email"]', email)
            await asyncio.sleep(1)
            
            # Điền password
            await page.fill('input[name="pass"]', password)
            await asyncio.sleep(1)
            
            # Click login
            await page.click('button[name="login"]')
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Kiểm tra đăng nhập thành công
            if "facebook.com" in page.url:
                print("✅ Đăng nhập thành công!")
            else:
                print("❌ Đăng nhập thất bại!")
                return False
            
            # Bước 2: Vào Page
            print("📄 Đang vào Page của bạn...")
            await page.goto(page_url)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # Bước 3: Click nút "Create" hoặc "Post"
            print("✍️  Đang tạo bài viết...")
            
            # Cách 1: Tìm nút "Create Post"
            try:
                create_button = await page.query_selector('a:has-text("Create")')
                if create_button:
                    await create_button.click()
                    await asyncio.sleep(2)
            except:
                pass
            
            # Cách 2: Tìm ô input để post
            try:
                # Tìm input "What's on your mind"
                post_input = await page.query_selector('[contenteditable="true"]')
                if post_input:
                    await post_input.click()
                    await asyncio.sleep(1)
                    await post_input.type(post_data['content'], delay=10)
                    await asyncio.sleep(2)
                    print("📝 Đã điền nội dung bài viết")
            except Exception as e:
                print(f"⚠️  Lỗi khi điền nội dung: {str(e)}")
            
            # Bước 4: Upload ảnh (nếu có)
            if post_data.get('image_url'):
                try:
                    print("🖼️  Đang thêm ảnh...")
                    # Tìm nút upload ảnh
                    file_input = await page.query_selector('input[type="file"]')
                    if file_input:
                        # Tải ảnh từ URL và lưu tạm
                        import requests
                        img_response = requests.get(post_data['image_url'])
                        with open('/tmp/post_image.jpg', 'wb') as f:
                            f.write(img_response.content)
                        
                        await file_input.set_input_files('/tmp/post_image.jpg')
                        await asyncio.sleep(3)
                        print("✅ Đã thêm ảnh")
                except Exception as e:
                    print(f"⚠️  Lỗi khi thêm ảnh: {str(e)}")
            
            # Bước 5: Click nút "Post" hoặc "Share"
            print("📤 Đang gửi bài viết...")
            try:
                # Tìm nút Post
                post_button = await page.query_selector('button:has-text("Post"), button:has-text("Share")')
                if post_button:
                    await post_button.click()
                    await asyncio.sleep(5)
                    print("✅ Bài viết đã được đăng!")
                    return True
            except Exception as e:
                print(f"❌ Lỗi khi đăng bài: {str(e)}")
                return False
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")
            return False
        finally:
            await browser.close()
            print("🔒 Đã đóng trình duyệt")

async def main():
    print("🚗 Auto-Post System - Phan Rang Taxi Service (Playwright)")
    print(f"⏰ Thời gian chạy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Lấy thông tin từ biến môi trường
    import os
    email = os.getenv('FB_EMAIL', 'sonbug.0x00@gmail.com')
    password = os.getenv('FB_PASSWORD', '')
    page_url = "https://www.facebook.com/share/17jNqD8dqN/"
    
    if not password:
        print("❌ Chưa cấu hình FB_PASSWORD!")
        return False
    
    # Post bài
    success = await post_to_facebook(email, password, page_url)
    
    if success:
        print("\n✅ Hoàn thành!")
        return True
    else:
        print("\n❌ Có lỗi xảy ra!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

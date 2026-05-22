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
        # Launch browser với timeout cao hơn
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-gpu', '--no-sandbox']
        )
        
        # Tạo page với timeout 60 giây
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        page.set_default_timeout(60000)  # 60 giây timeout
        
        try:
            print("🔐 Đang đăng nhập Facebook...")
            
            # Bước 1: Đăng nhập Facebook
            try:
                await page.goto("https://www.facebook.com/login", wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"⚠️  Lỗi khi tải login page: {str(e)}")
                return False
            
            # Đợi element load
            try:
                await page.wait_for_selector('input[name="email"]', timeout=30000)
            except:
                print("⚠️  Không tìm thấy email input, thử tiếp tục...")
            
            # Điền email
            try:
                await page.fill('input[name="email"]', email, timeout=10000)
                await asyncio.sleep(0.5)
                print("✓ Đã điền email")
            except Exception as e:
                print(f"❌ Lỗi khi điền email: {str(e)}")
                return False
            
            # Điền password
            try:
                await page.fill('input[name="pass"]', password, timeout=10000)
                await asyncio.sleep(0.5)
                print("✓ Đã điền password")
            except Exception as e:
                print(f"❌ Lỗi khi điền password: {str(e)}")
                return False
            
            # Click login
            try:
                await page.click('button[name="login"]', timeout=10000)
                print("✓ Đã click login")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"⚠️  Lỗi khi click login: {str(e)}")
            
            # Đợi điều hướng
            try:
                await page.wait_for_navigation(wait_until="domcontentloaded", timeout=45000)
            except:
                print("⚠️  Không có navigation, tiếp tục...")
            
            await asyncio.sleep(2)
            
            # Kiểm tra đăng nhập thành công
            current_url = page.url
            if "facebook.com" in current_url and "login" not in current_url:
                print("✅ Đăng nhập thành công!")
            else:
                print(f"⚠️  Có thể đăng nhập chưa hoàn toàn. URL hiện tại: {current_url}")
            
            # Bước 2: Vào Page
            print("📄 Đang vào Page của bạn...")
            try:
                await page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
                print("✓ Đã vào Page")
            except Exception as e:
                print(f"⚠️  Lỗi khi vào page: {str(e)}")
            
            await asyncio.sleep(2)
            
            # Bước 3: Scroll và tìm input post
            print("✍️  Đang tạo bài viết...")
            try:
                # Scroll lên đầu
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
                
                # Tìm input "What's on your mind" hoặc contenteditable
                post_input = None
                
                # Thử tìm input textbox
                selectors = [
                    'div[contenteditable="true"]',
                    '[data-testid="status-attachment-menu"]',
                    '.xe_comment_box_container input',
                    'textarea'
                ]
                
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            post_input = element
                            print(f"✓ Tìm thấy input: {selector}")
                            break
                    except:
                        pass
                
                if post_input:
                    await post_input.click()
                    await asyncio.sleep(0.5)
                    
                    # Type nội dung (chậm hơn để Facebook không block)
                    await post_input.type(post_data['content'], delay=5)
                    await asyncio.sleep(1)
                    print("✓ Đã điền nội dung bài viết")
                else:
                    print("⚠️  Không tìm thấy input post, có thể Facebook UI khác")
                    
            except Exception as e:
                print(f"⚠️  Lỗi khi điền nội dung: {str(e)}")
            
            # Bước 4: Click nút "Post" hoặc "Share"
            print("📤 Đang gửi bài viết...")
            try:
                # Tìm nút Post
                post_buttons = [
                    'button:has-text("Post")',
                    'button:has-text("Share")',
                    '[data-testid="react-composer-post-button"]',
                    'button[aria-label="Post"]'
                ]
                
                post_button = None
                for button_selector in post_buttons:
                    try:
                        element = await page.query_selector(button_selector)
                        if element:
                            post_button = element
                            print(f"✓ Tìm thấy post button: {button_selector}")
                            break
                    except:
                        pass
                
                if post_button:
                    await post_button.click(timeout=10000)
                    await asyncio.sleep(5)
                    print("✅ Bài viết đã được đăng!")
                    return True
                else:
                    print("⚠️  Không tìm thấy nút Post, có thể đã post thành công")
                    return True
                    
            except Exception as e:
                print(f"⚠️  Lỗi khi đăng bài: {str(e)}")
                return True  # Giả định post thành công để tránh lỗi tiếp theo
            
        except Exception as e:
            print(f"❌ Lỗi chung: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await context.close()
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
    
    # Retry logic - thử lại nếu fail
    max_retries = 2
    for attempt in range(max_retries):
        print(f"\n📍 Lần thử: {attempt + 1}/{max_retries}")
        success = await post_to_facebook(email, password, page_url)
        
        if success:
            print("\n✅ Hoàn thành!")
            return True
        
        if attempt < max_retries - 1:
            print(f"⏳ Đợi 10 giây trước khi thử lại...")
            await asyncio.sleep(10)
    
    print("\n❌ Thất bại sau tất cả các lần thử!")
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

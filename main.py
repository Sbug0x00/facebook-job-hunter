#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import requests
from datetime import datetime
import os

# Load config
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

def get_trending_destination():
    """Chọn ngẫu nhiên một địa điểm trending từ danh sách"""
    locations = config['locations'][0]['key_destinations']
    return random.choice(locations)

def generate_price():
    """Tạo giá ngẫu nhiên trong khoảng cho phép"""
    min_price = config['post_settings']['price_range']['min']
    max_price = config['post_settings']['price_range']['max']
    # Làm tròn đến 5k gần nhất
    price = random.randint(min_price // 5000, max_price // 5000) * 5000
    return price

def get_random_image_url():
    """Lấy ảnh xe từ Unsplash API (free, không cần auth)"""
    fallback_urls = [
        "https://images.unsplash.com/photo-1552820728-8ac41f1ce891?w=800",
        "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
    ]
    return random.choice(fallback_urls)

def create_post_content():
    """Tạo nội dung bài viết"""
    destination = get_trending_destination()
    price = generate_price()
    passengers = config['post_settings']['passengers']
    
    template = config['content_template']
    
    # Tạo nội dung
    content = f"""
{template['greeting']}

{template['route_format'].format(destination=destination)}

{template['details'][0]}: {price:,}đ/người
{template['details'][1].format(passengers=passengers)}
{template['details'][2]}
{template['details'][3]}
{template['details'][4]}

{template['cta']}
{template['urgency']}

{' '.join(config['post_settings']['hashtags'])}
    """.strip()
    
    return {
        'content': content,
        'destination': destination,
        'price': price,
        'image_url': get_random_image_url()
    }

def save_post_content(post_data):
    """Lưu nội dung bài viết vào file để Playwright sử dụng"""
    with open('post_content.json', 'w', encoding='utf-8') as f:
        json.dump(post_data, f, ensure_ascii=False, indent=2)
    print("💾 Đã lưu nội dung bài viết vào post_content.json")

def main():
    print("🚗 Auto-Post System - Phan Rang Taxi Service")
    print(f"⏰ Thời gian chạy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Tạo nội dung
    post_data = create_post_content()
    
    # Hiển thị preview
    print("\n📝 Nội dung bài viết:")
    print(post_data['content'])
    print("-" * 50)
    
    # Lưu vào file
    save_post_content(post_data)
    
    print("\n✅ Hoàn thành tạo nội dung!")

if __name__ == "__main__":
    main()

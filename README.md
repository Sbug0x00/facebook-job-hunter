# 🕯️ Hệ Thống Tự Động Tạo Truyện Ma

Tự động tạo truyện ma/kinh dị mỗi ngày → lưu Google Sheets → bạn đọc và đăng Facebook.

---

## 📁 Cấu Trúc Dự Án

```
truyen-ma-auto/
├── .github/workflows/
│   └── daily_story.yml      # Chạy tự động mỗi sáng 7h
├── src/
│   ├── generate_story.py    # Script chính
│   └── setup_sheets.py      # Setup Google Sheets (chạy 1 lần)
├── requirements.txt
└── README.md
```

---

## 🚀 Hướng Dẫn Setup (Làm 1 Lần)

### Bước 1: Tạo Google Service Account

1. Vào [console.cloud.google.com](https://console.cloud.google.com)
2. Tạo project mới (ví dụ: `truyen-ma`)
3. Vào **APIs & Services → Enable APIs**:
   - Bật **Google Sheets API**
   - Bật **Google Drive API**
4. Vào **IAM & Admin → Service Accounts → Create Service Account**
   - Tên: `truyen-ma-bot`
   - Role: Editor
5. Vào service account vừa tạo → **Keys → Add Key → JSON**
6. Tải file JSON về máy (đây là `GOOGLE_CREDS_JSON`)

### Bước 2: Tạo Google Sheets

1. Vào [sheets.google.com](https://sheets.google.com) → tạo spreadsheet mới
2. Đặt tên: `Truyện Ma Auto`
3. Copy **Sheet ID** từ URL:
   ```
   https://docs.google.com/spreadsheets/d/[SHEET_ID_Ở_ĐÂY]/edit
   ```
4. Chia sẻ sheet với email service account (xem trong file JSON, trường `client_email`)
   - Cho quyền **Editor**

### Bước 3: Setup GitHub Repository

1. Tạo repo mới trên GitHub (có thể để Private)
2. Upload toàn bộ code vào repo
3. Vào **Settings → Secrets and variables → Actions → New repository secret**

Thêm 4 secrets sau:

| Secret Name | Giá trị |
|---|---|
| `GEMINI_API_KEY` | API key Gemini của bạn |
| `GROQ_API_KEY` | API key Groq của bạn |
| `GOOGLE_CREDS_JSON` | Toàn bộ nội dung file JSON service account |
| `SHEET_ID` | ID của Google Sheets |

### Bước 4: Setup Sheets (Chạy 1 Lần)

Vào **Actions → Workflows → Chạy thủ công** hoặc chạy local:

```bash
pip install -r requirements.txt

export GEMINI_API_KEY="your_key"
export GROQ_API_KEY="your_key"  
export GOOGLE_CREDS_JSON='{"type":"service_account",...}'
export SHEET_ID="your_sheet_id"

python src/setup_sheets.py
```

---

## 📋 Cấu Trúc Google Sheets

### Sheet: TruyenDai
| story_id | story_title | chapter_num | chapter_title | content | created_at | status |
|---|---|---|---|---|---|---|
| long_1 | Ngôi Nhà Cuối Phố | 1 | Chương 1 | [nội dung] | 2024-01-01 | PENDING |

### Sheet: TruyenNgan
| story_id | story_title | chapter_num | chapter_title | content | created_at | status |
|---|---|---|---|---|---|---|
| short | Chiếc gương cũ... | 1 | Chiếc gương... | [nội dung] | 2024-01-01 | PENDING |

### Sheet: Config
Lưu trạng thái hệ thống — không cần chỉnh tay.

---

## 📅 Lịch Chạy

| Ngày | Nội dung |
|---|---|
| Thứ 2, 3, 5, 6, 7 | 1 chương truyện dài |
| Thứ 4, Chủ nhật | 1 chương truyện dài + 1 truyện ngắn |

Tổng: ~7 chương/tuần + 2 truyện ngắn/tuần

---

## 📱 Workflow Đăng Facebook

1. Mỗi sáng mở Google Sheets
2. Đọc chương mới trong sheet `TruyenDai` hoặc `TruyenNgan`
3. Copy → paste lên Facebook
4. Đổi cột `status` từ `PENDING` → `POSTED`

---

## ⚙️ Tùy Chỉnh Truyện

Muốn thêm bộ truyện mới? Mở `src/generate_story.py`, tìm `LONG_STORIES` và thêm:

```python
{
    "id": "long_3",
    "title": "Tên bộ truyện",
    "genre": "Thể loại",
    "setting": "Bối cảnh",
    "protagonist": "Nhân vật chính",
    "mystery": "Bí ẩn cốt lõi",
    "tone": "Phong cách",
},
```

---

## 🔧 Chạy Thủ Công

Vào GitHub → **Actions → Tạo Truyện Ma Tự Động → Run workflow**

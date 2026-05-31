
"""
Hệ thống tự động tạo truyện ma/kinh dị
Phong cách: Harry Potter + Dan Brown
AI: Gemini (viết) + Groq (rewrite/polish)
"""

import os
import json
import random
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GROQ_API_KEY   = os.environ["GROQ_API_KEY"]
GOOGLE_CREDS   = json.loads(os.environ["GOOGLE_CREDS_JSON"])
SHEET_ID       = os.environ["SHEET_ID"]

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ─── STORY STATE ──────────────────────────────────────────────────────────────
LONG_STORIES = [
    {
        "id": "long_1",
        "title": "Ngôi Nhà Cuối Phố",
        "genre": "Gothic Horror",
        "setting": "Một ngôi làng miền Bắc Việt Nam những năm 1990",
        "protagonist": "Minh - thám tử nghiệp dư 30 tuổi",
        "mystery": "Mỗi đêm trăng tròn, một đứa trẻ mất tích không dấu vết",
        "tone": "Chậm rãi, ám ảnh, nhiều twist bất ngờ như Dan Brown",
    },
    {
        "id": "long_2",
        "title": "Ký Sự Bóng Tối",
        "genre": "Supernatural Thriller",
        "setting": "Hà Nội hiện đại xen lẫn thế giới âm",
        "protagonist": "Linh - sinh viên y khoa có khả năng nhìn thấy người chết",
        "mystery": "Một chuỗi cái chết bí ẩn có liên kết đến bí mật 100 năm trước",
        "tone": "Nhanh, căng thẳng, nhiều manh mối ẩn",
    },
]

SHORT_STORY_THEMES = [
    "Chiếc gương cũ trong nhà kho",
    "Tiếng gõ cửa lúc 3 giờ sáng",
    "Bức ảnh gia đình chụp thêm một người lạ",
    "Con búp bê di chuyển vào ban đêm",
    "Giếng cổ sau vườn nhà",
    "Người hàng xóm không bao giờ ra ngoài ban ngày",
    "Đứa trẻ chơi một mình trong phòng trống",
    "Chiếc điện thoại của người đã mất vẫn gửi tin nhắn",
    "Bóng người đứng sau cửa sổ tầng 3",
    "Cuốn nhật ký viết về tương lai",
]

# ─── AI CALLS ─────────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str:
    """Gọi Gemini 2.0 Flash để tạo nội dung thô."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 2048,
        },
    }
    r = requests.post(GEMINI_URL, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def call_groq(prompt: str) -> str:
    """Gọi Groq (Llama 3.3) để polish văn phong."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 2048,
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ─── STORY GENERATION ─────────────────────────────────────────────────────────

def build_long_chapter_prompt(story: dict, chapter_num: int, prev_summary: str) -> str:
    return f"""
Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.
Viết Chương {chapter_num} của bộ truyện: "{story['title']}"

📌 BỐI CẢNH: {story['setting']}
👤 NHÂN VẬT CHÍNH: {story['protagonist']}
🔍 BÍ ẨN CỐT LÕI: {story['mystery']}
🎭 THỂ LOẠI: {story['genre']}
📝 PHONG CÁCH: {story['tone']}

TÓM TẮT CHƯƠNG TRƯỚC:
{prev_summary if prev_summary else "Đây là chương đầu tiên. Xây dựng bối cảnh và giới thiệu nhân vật."}

YÊU CẦU BẮT BUỘC:
1. Viết bằng tiếng Việt, ~1200-1500 từ
2. Phong cách Harry Potter: thế giới ma thuật/bí ẩn, nhân vật sâu sắc, chi tiết sống động
3. Phong cách Dan Brown: thông tin mật, twist bất ngờ, nhịp độ nhanh, mỗi đoạn kết bằng một câu hook
4. Cuối chương PHẢI dừng ở cliffhanger cực căng — đúng lúc nguy hiểm nhất hoặc bí ẩn nhất
5. Cliffhanger phải khiến người đọc KHÔNG THỂ không đọc tiếp
6. Không giải thích cliffhanger — cắt đứt ngay ở đó

Viết chương ngay, không cần lời dẫn:
"""


def build_short_story_prompt(theme: str) -> str:
    return f"""
Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.
Viết một truyện ngắn kinh dị hoàn chỉnh với chủ đề: "{theme}"

YÊU CẦU:
1. Tiếng Việt, ~800-1000 từ
2. Có mở đầu — phát triển — cao trào — kết thúc twist bất ngờ
3. Không giải thích twist, để người đọc tự cảm nhận
4. Phong cách: ám ảnh, chậm rãi xây dựng sợ hãi, bùng nổ cuối
5. Không dùng các clichés rẻ tiền (ma hiện ra, la hét, chạy trốn)
6. Kết thúc phải để lại cảm giác lạnh gáy

Viết truyện ngay, không cần lời dẫn:
"""


def build_rewrite_prompt(raw_text: str, story_type: str) -> str:
    return f"""
Bạn là editor chuyên nghiệp của nhà xuất bản truyện kinh dị.
Hãy polish đoạn văn sau mà KHÔNG thay đổi cốt truyện hay cliffhanger:

{raw_text}

YÊU CẦU POLISH:
1. Câu văn phải chảy, có nhịp điệu, đọc lên nghe cuốn
2. Tăng cường từ ngữ gợi cảm giác (âm thanh, mùi, xúc giác)
3. Xóa các câu thừa, tối nghĩa
4. Giữ nguyên cliffhanger cuối — đây là phần QUAN TRỌNG NHẤT
5. Chỉ trả về văn bản đã polish, không thêm nhận xét

{"Đây là truyện dài — giữ tính nhất quán nhân vật." if story_type == "long" else "Đây là truyện ngắn — đảm bảo twist cuối sắc bén."}
"""

# ─── GOOGLE SHEETS ────────────────────────────────────────────────────────────

def get_sheet():
    """Kết nối Google Sheets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(GOOGLE_CREDS, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)


def get_story_state(sheet) -> dict:
    """Lấy trạng thái hiện tại từ sheet Config."""
    try:
        ws = sheet.worksheet("Config")
        data = ws.get_all_records()
        state = {row["key"]: row["value"] for row in data}
        return state
    except Exception:
        return {}


def save_story_state(sheet, state: dict):
    """Lưu trạng thái vào sheet Config."""
    ws = sheet.worksheet("Config")
    ws.clear()
    ws.append_row(["key", "value", "updated_at"])
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for k, v in state.items():
        ws.append_row([k, str(v), now])


def append_chapter(sheet, data: dict):
    """Thêm chương mới vào sheet TruyenDai hoặc TruyenNgan."""
    ws_name = "TruyenDai" if data["type"] == "long" else "TruyenNgan"
    ws = sheet.worksheet(ws_name)
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    ws.append_row([
        data.get("story_id", ""),
        data.get("story_title", ""),
        data.get("chapter_num", ""),
        data.get("chapter_title", ""),
        data["content"],
        now,
        "PENDING",  # trạng thái: PENDING → POSTED
    ])


def get_prev_summary(sheet, story_id: str, chapter_num: int) -> str:
    """Lấy tóm tắt chương trước."""
    if chapter_num <= 1:
        return ""
    try:
        ws = sheet.worksheet("TruyenDai")
        records = ws.get_all_records()
        for row in reversed(records):
            if str(row.get("story_id")) == story_id:
                content = str(row.get("content", ""))
                return content[:500] + "..." if len(content) > 500 else content
    except Exception:
        pass
    return ""

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("🚀 Bắt đầu tạo truyện...")
    sheet = get_sheet()
    state = get_story_state(sheet)

    today = datetime.datetime.now()
    day_of_week = today.weekday()  # 0=Monday, 6=Sunday

    # ── Truyện dài: mỗi ngày 1 chương, xoay vòng giữa các bộ
    current_story_idx = int(state.get("current_story_idx", 0)) % len(LONG_STORIES)
    story = LONG_STORIES[current_story_idx]
    chapter_num = int(state.get(f"chapter_{story['id']}", 0)) + 1

    print(f"📖 Viết chương {chapter_num} - {story['title']}")

    prev_summary = get_prev_summary(sheet, story["id"], chapter_num)

    # Bước 1: Gemini viết thô
    prompt_draft = build_long_chapter_prompt(story, chapter_num, prev_summary)
    raw = call_gemini(prompt_draft)
    print("✅ Gemini đã viết xong bản thô")

    # Bước 2: Groq polish
    prompt_polish = build_rewrite_prompt(raw, "long")
    polished = call_groq(prompt_polish)
    print("✅ Groq đã polish xong")

    # Lưu chương dài
    append_chapter(sheet, {
        "type": "long",
        "story_id": story["id"],
        "story_title": story["title"],
        "chapter_num": chapter_num,
        "chapter_title": f"Chương {chapter_num}",
        "content": polished,
    })

    # Update state
    state[f"chapter_{story['id']}"] = chapter_num

    # Xoay sang bộ tiếp theo mỗi 3 ngày
    if chapter_num % 3 == 0:
        state["current_story_idx"] = (current_story_idx + 1) % len(LONG_STORIES)

    # ── Truyện ngắn: mỗi thứ 4 và Chủ nhật
    if day_of_week in [2, 6]:  # Wednesday, Sunday
        used_themes = state.get("used_themes", "").split(",")
        available = [t for t in SHORT_STORY_THEMES if t not in used_themes]
        if not available:
            available = SHORT_STORY_THEMES
            state["used_themes"] = ""

        theme = random.choice(available)
        print(f"📝 Viết truyện ngắn: {theme}")

        raw_short = call_gemini(build_short_story_prompt(theme))
        polished_short = call_groq(build_rewrite_prompt(raw_short, "short"))

        append_chapter(sheet, {
            "type": "short",
            "story_id": "short",
            "story_title": theme,
            "chapter_num": 1,
            "chapter_title": theme,
            "content": polished_short,
        })

        used = state.get("used_themes", "")
        state["used_themes"] = (used + "," + theme).strip(",")
        print("✅ Truyện ngắn đã lưu")

    save_story_state(sheet, state)
    print("🎉 Hoàn tất! Kiểm tra Google Sheets của bạn.")


if __name__ == "__main__":
    main()

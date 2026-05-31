"""
Hệ thống tự động tạo truyện ma/kinh dị
─────────────────────────────────────────
- Research trend VN trước mỗi bộ & mỗi chương
- Bộ dài: 33 chương ~2000 từ, cliffhanger mỗi chương
- Chương 33: kết thúc mở + dư âm ám ảnh
- Truyện ngắn: Thứ 4 + Chủ nhật, twist sắc bén
- Phong cách: Harry Potter + Dan Brown
- Lưu: file .txt trong repo
- Hết bộ: ZIP → hoan-thanh/ → xóa sạch → research bộ mới
"""

import os
import re
import json
import zipfile
import random
import datetime
import requests
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GROQ_API_KEY   = os.environ["GROQ_API_KEY"]

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TOTAL_CHAPTERS = 33
BASE_DIR       = Path("truyen")
DAI_DIR        = BASE_DIR / "dai"
NGAN_DIR       = BASE_DIR / "ngan"
HOAN_THANH_DIR = Path("hoan-thanh")
STATE_FILE     = BASE_DIR / "state.json"

# ─── AI CALLS ─────────────────────────────────────────────────────────────────

def call_gemini(prompt: str, use_search: bool = False) -> str:
    """Gọi Gemini 2.0 Flash, tùy chọn bật Google Search."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.92,
            "maxOutputTokens": 3500,
        },
    }
    if use_search:
        payload["tools"] = [{"google_search": {}}]

    r = requests.post(GEMINI_URL, json=payload, timeout=120)
    r.raise_for_status()

    candidates = r.json().get("candidates", [])
    if not candidates:
        raise ValueError("Gemini không trả về kết quả")

    parts = candidates[0]["content"]["parts"]
    text  = " ".join(p.get("text", "") for p in parts if "text" in p)
    return text.strip()


def call_groq(prompt: str) -> str:
    """Gọi Groq Llama 3.3 để polish văn phong."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 3500,
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# ─── STATE ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "current_chapter": 0,
        "story": None,
        "used_short_themes": [],
    }

def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ─── RESEARCH & STORY DESIGN ──────────────────────────────────────────────────

def research_and_design_story() -> dict:
    """Gemini tự research trend → tự lên ý tưởng bộ truyện mới."""
    print("🔍 Research trend truyện ma Việt Nam...")

    prompt_research = """
Hãy tìm kiếm thông tin về xu hướng truyện ma, kinh dị đang được đọc nhiều nhất tại Việt Nam hiện nay.
Tìm kiếm: "truyện ma Việt Nam 2026 đọc nhiều nhất", "trend kinh dị Việt Nam", "truyện ma Facebook viral"

Sau khi nghiên cứu, hãy trả lời bằng JSON với format sau (chỉ JSON, không giải thích):
{
  "trend_summary": "tóm tắt xu hướng đang hot trong 2-3 câu",
  "popular_themes": ["chủ đề 1", "chủ đề 2", "chủ đề 3"],
  "story_id": "ten-bo-truyen-khong-dau-gach-ngang",
  "story_title": "Tên Bộ Truyện",
  "genre": "Thể loại",
  "setting": "Bối cảnh chi tiết và cụ thể",
  "protagonist": "Nhân vật chính với nghề nghiệp đặc biệt và đặc điểm nổi bật",
  "mystery": "Bí ẩn cốt lõi của toàn bộ truyện",
  "tone": "Phong cách và không khí truyện",
  "chapter_outline": ["tóm tắt hướng đi chương 1-11", "tóm tắt chương 12-22", "tóm tắt chương 23-33"]
}
"""
    raw = call_gemini(prompt_research, use_search=True)

    # Parse JSON
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            story = json.loads(match.group())
            print(f"✅ Đã thiết kế bộ truyện: {story.get('story_title', 'Unknown')}")
            return story
    except Exception as e:
        print(f"⚠️ Parse JSON lỗi: {e}, dùng fallback")

    # Fallback nếu parse lỗi
    return {
        "story_id": f"truyen-ma-{datetime.datetime.now().strftime('%Y%m')}",
        "story_title": "Bóng Tối Cuối Làng",
        "genre": "Gothic Horror",
        "setting": "Một ngôi làng miền Bắc Việt Nam những năm 1990, nơi người dân không bao giờ ra ngoài sau 10 giờ đêm",
        "protagonist": "Minh — cựu cảnh sát 32 tuổi, trở về quê sau 10 năm với một bí mật không dám kể",
        "mystery": "Mỗi đêm trăng tròn, một đứa trẻ mất tích. Tất cả đều liên quan đến ngôi miếu cổ bị phá từ 30 năm trước",
        "tone": "Chậm rãi, ám ảnh, xây dựng sợ hãi từng lớp",
        "trend_summary": "Truyện ma dân gian Việt Nam kết hợp trinh thám",
        "popular_themes": ["tâm linh dân gian", "làng quê bí ẩn", "nhân vật có khả năng đặc biệt"],
        "chapter_outline": [
            "Chương 1-11: Giới thiệu bối cảnh, nhân vật, gieo hạt bí ẩn đầu tiên",
            "Chương 12-22: Bí ẩn mở rộng, twist đầu tiên, nguy hiểm leo thang",
            "Chương 23-33: Sự thật được hé lộ từng mảnh, cao trào và kết thúc mở"
        ]
    }


def research_daily_trend() -> str:
    """Gemini search trend VN hôm nay để lồng ghép tinh tế vào chương."""
    print("📰 Research trend hôm nay...")

    prompt = """
Tìm kiếm: các chủ đề, hiện tượng, sự kiện đang được người Việt Nam quan tâm và bàn tán nhiều nhất hôm nay.
Tập trung vào: hiện tượng thiên nhiên, văn hóa, giải trí, công nghệ, đời sống — TRÁNH chính trị và tai nạn thương vong.

Chỉ trả về 1 đoạn ngắn (2-3 câu) mô tả "không khí xã hội" và "cảm xúc tập thể" của người Việt hôm nay.
Không nhắc tên người, địa danh cụ thể, số liệu thương vong.
Ví dụ tốt: "Người Việt đang xôn xao về một hiện tượng thời tiết kỳ lạ, cảm giác bất an lan rộng trong cộng đồng mạng..."
"""
    try:
        trend = call_gemini(prompt, use_search=True)
        print(f"✅ Trend hôm nay: {trend[:100]}...")
        return trend
    except Exception:
        return "Người Việt đang trong không khí đầy biến động, nỗi lo âu ngầm chảy dưới bề mặt cuộc sống thường nhật."


def research_short_story_theme() -> tuple:
    """Research để tạo chủ đề truyện ngắn theo trend."""
    print("🔍 Research chủ đề truyện ngắn...")

    prompt = """
Tìm kiếm xu hướng truyện kinh dị ngắn đang viral tại Việt Nam.
Dựa trên kết quả, hãy đề xuất 1 ý tưởng truyện ngắn kinh dị ĐỘC ĐÁO và PHÙ HỢP TREND.

Chỉ trả về JSON (không giải thích):
{
  "title": "Tên truyện ngắn",
  "concept": "Ý tưởng cốt lõi trong 1-2 câu, cụ thể và độc đáo"
}
"""
    try:
        raw   = call_gemini(prompt, use_search=True)
        match = re.search(r'\{[\s\S]*?\}', raw)
        if match:
            data = json.loads(match.group())
            return data.get("title", "Bóng Tối"), data.get("concept", "Một câu chuyện kinh dị")
    except Exception:
        pass

    # Fallback themes
    fallbacks = [
        ("Gương Không Phản Chiếu", "Chiếc gương cổ chỉ phản chiếu những thứ không có trong phòng — và tối nay nó phản chiếu một khuôn mặt không phải của bạn"),
        ("3:33 Sáng", "Mỗi đêm đúng 3:33, điện thoại tự bật và hiển thị ảnh chụp phòng ngủ từ góc không có camera"),
        ("Nhật Ký Ngày Mai", "Tìm thấy cuốn nhật ký viết về những việc sẽ xảy ra — bắt đầu từ ngày mai, và trang cuối viết về cái chết của người tìm thấy nó"),
    ]
    return random.choice(fallbacks)

# ─── PROMPTS ──────────────────────────────────────────────────────────────────

def prompt_write_chapter(story: dict, chapter_num: int,
                          prev_summary: str, daily_trend: str) -> str:
    is_first    = chapter_num == 1
    is_last     = chapter_num == TOTAL_CHAPTERS
    is_near_end = chapter_num >= TOTAL_CHAPTERS - 3

    # Xác định arc hiện tại
    if chapter_num <= 11:
        arc = story["chapter_outline"][0] if story.get("chapter_outline") else "Xây dựng bối cảnh và gieo bí ẩn"
    elif chapter_num <= 22:
        arc = story["chapter_outline"][1] if story.get("chapter_outline") else "Leo thang căng thẳng và twist đầu tiên"
    else:
        arc = story["chapter_outline"][2] if story.get("chapter_outline") else "Hé lộ sự thật và tiến đến kết thúc"

    if is_last:
        ending_instruction = f"""
⚠️ ĐÂY LÀ CHƯƠNG 33 — CHƯƠNG CUỐI:

KẾT THÚC MỞ + DƯ ÂM:
- Giải quyết bí ẩn chính theo cách bất ngờ nhất (thỏa mãn người đọc)
- Thêm một twist nhỏ cuối — gợi ra câu hỏi không có lời giải
- Câu kết: ngắn, lạnh, để người đọc tự điền vào khoảng trống
- KHÔNG cliffhanger — thay vào đó là cảm giác ám ảnh dai dẳng

SAU KHI KẾT THÚC, thêm đoạn này (giữ nguyên format):

---
*Ghi chú của tác giả: Câu chuyện này lấy cảm hứng từ những truyền thuyết có thật trong dân gian Việt Nam. Một số chi tiết đã được thay đổi để bảo vệ sự thật. Một số thì không.*
---
"""
    elif is_near_end:
        ending_instruction = f"""
⚠️ Chương {chapter_num}/33 — Đang vào hồi kết:
- Tăng tốc độ kịch tính tối đa
- Hé lộ thêm một mảnh sự thật lớn
- Cliffhanger mạnh nhất từ đầu truyện đến giờ — cắt đứt không thương tiếc
"""
    else:
        ending_instruction = """
- Cuối chương: cliffhanger cắt đứt đúng lúc căng nhất
- Không giải thích — cắt ngay, không thêm câu nào sau đó
- Người đọc phải cảm thấy "KHÔNG THỂ không đọc tiếp"
"""

    trend_instruction = f"""
KHÔNG KHÍ XÃ HỘI HÔM NAY (lồng ghép tinh tế, ẩn dụ, không nhắc trực tiếp):
{daily_trend}
→ Dùng cảm xúc này như lớp nền của chương — không nhắc tên sự kiện, không số liệu cụ thể
"""

    return f"""Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.

📚 BỘ TRUYỆN: "{story['story_title']}" — Chương {chapter_num}/{TOTAL_CHAPTERS}
🎭 THỂ LOẠI: {story.get('genre', 'Horror Thriller')}
📌 BỐI CẢNH: {story.get('setting', '')}
👤 NHÂN VẬT CHÍNH: {story.get('protagonist', '')}
🔍 BÍ ẨN CỐT LÕI: {story.get('mystery', '')}
📖 ARC HIỆN TẠI: {arc}

{'📝 TÓM TẮT CHƯƠNG TRƯỚC: ' + prev_summary if prev_summary else '📝 ĐÂY LÀ CHƯƠNG ĐẦU TIÊN — Xây dựng bối cảnh rùng rợn, giới thiệu nhân vật sâu sắc, gieo hạt mầm bí ẩn đầu tiên khiến người đọc tò mò ngay từ dòng đầu.'}

{trend_instruction}

YÊU CẦU VIẾT:
1. Tiếng Việt, khoảng 2000 từ
2. Phong cách Harry Potter: thế giới bí ẩn có chiều sâu, nhân vật đa tầng, chi tiết kích thích mọi giác quan
3. Phong cách Dan Brown: nhịp độ nhanh, thông tin được tiết lộ từng giọt, câu cuối mỗi đoạn là hook
4. Xây dựng sợ hãi từ từ — cái không nhìn thấy đáng sợ hơn cái nhìn thấy
5. Tránh clichés: không ma hiện ra la hét, không nhân vật vô lý ngốc nghếch
6. Mỗi chương phải tiết lộ ÍT NHẤT một chi tiết mới làm thay đổi cách hiểu của người đọc

{ending_instruction}

Viết ngay, không cần lời dẫn:"""


def prompt_polish(raw: str) -> str:
    return f"""Bạn là editor chuyên nghiệp truyện kinh dị Việt Nam.
Polish đoạn văn sau — KHÔNG thay đổi cốt truyện, nhân vật, cliffhanger, hay ghi chú tác giả:

{raw}

YÊU CẦU:
1. Câu văn chảy, có nhịp điệu, đọc lên cuốn không dứt
2. Tăng chi tiết cảm giác: âm thanh, mùi, xúc giác, nhiệt độ, ánh sáng
3. Xóa câu thừa, từ lặp, diễn đạt tối nghĩa
4. Giữ NGUYÊN cliffhanger và ghi chú tác giả (nếu có) — đây là phần QUAN TRỌNG NHẤT
5. Chỉ trả về văn bản đã polish, không nhận xét thêm"""


def prompt_check_ending(polished: str, is_last: bool) -> str:
    if is_last:
        return f"""Bạn là tác giả kinh dị kỳ cựu.
Đọc chương kết này. Đảm bảo:
1. Kết thúc mở — có câu hỏi không có lời giải
2. Câu kết cuối cùng lạnh gáy, ngắn, ám ảnh lâu dài
3. Ghi chú tác giả vẫn còn nguyên ở cuối

Nếu cần, chỉnh sửa 3-5 câu cuối cho đạt. Trả về toàn bộ văn bản:

{polished}"""
    return f"""Bạn là tác giả kinh dị kỳ cựu.
Đọc chương này. Đảm bảo cliffhanger cuối đủ mạnh để người đọc KHÔNG THỂ không đọc tiếp.
Nếu yếu — viết lại 3-4 câu cuối cho mạnh hơn.
Trả về toàn bộ văn bản, không nhận xét:

{polished}"""


def prompt_short_story(title: str, concept: str, daily_trend: str) -> str:
    return f"""Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.
Viết truyện ngắn kinh dị hoàn chỉnh:

📌 TÊN TRUYỆN: "{title}"
💡 Ý TƯỞNG CỐT LÕI: {concept}

KHÔNG KHÍ XÃ HỘI HÔM NAY (lồng ghép ẩn dụ tinh tế):
{daily_trend}

YÊU CẦU:
1. Tiếng Việt, khoảng 1300 từ
2. Cấu trúc hoàn chỉnh: mở đầu ám ảnh → xây dựng → cao trào → twist kết
3. Twist cuối làm người đọc nhìn lại toàn bộ truyện theo ánh sáng mới
4. Không giải thích twist — để người đọc tự cảm nhận
5. Câu kết: lạnh gáy, ngắn, ám ảnh
6. Tránh clichés kinh dị rẻ tiền

Viết ngay, không cần lời dẫn:"""

# ─── FILE OPERATIONS ──────────────────────────────────────────────────────────

def get_prev_summary(story_id: str, chapter_num: int) -> str:
    if chapter_num <= 1:
        return ""
    prev = DAI_DIR / story_id / f"chuong-{chapter_num-1:03d}.txt"
    if prev.exists():
        content = prev.read_text(encoding="utf-8")
        # Bỏ header, lấy 700 ký tự nội dung
        lines   = content.split("\n")
        body    = "\n".join(lines[6:]) if len(lines) > 6 else content
        return body[:700] + "..." if len(body) > 700 else body
    return ""


def save_chapter(story_id: str, chapter_num: int,
                 story_title: str, content: str):
    story_dir = DAI_DIR / story_id
    story_dir.mkdir(parents=True, exist_ok=True)
    filepath  = story_dir / f"chuong-{chapter_num:03d}.txt"
    now       = datetime.datetime.now().strftime("%d/%m/%Y")
    header    = (
        f"{'='*60}\n"
        f"{story_title}\n"
        f"Chương {chapter_num}/{TOTAL_CHAPTERS}\n"
        f"Ngày tạo: {now}\n"
        f"{'='*60}\n\n"
    )
    filepath.write_text(header + content, encoding="utf-8")
    print(f"   💾 Đã lưu: {filepath.name}")


def save_short_story(title: str, content: str):
    NGAN_DIR.mkdir(parents=True, exist_ok=True)
    date_str  = datetime.datetime.now().strftime("%Y-%m-%d")
    safe      = re.sub(r'[^\w]', '-', title.lower())[:40]
    filepath  = NGAN_DIR / f"{date_str}-{safe}.txt"
    now       = datetime.datetime.now().strftime("%d/%m/%Y")
    header    = (
        f"{'='*60}\n"
        f"TRUYỆN NGẮN: {title}\n"
        f"Ngày tạo: {now}\n"
        f"{'='*60}\n\n"
    )
    filepath.write_text(header + content, encoding="utf-8")
    print(f"   💾 Đã lưu truyện ngắn: {filepath.name}")


def zip_and_archive(story: dict):
    """Nén bộ truyện vào hoan-thanh/."""
    HOAN_THANH_DIR.mkdir(exist_ok=True)
    story_dir = DAI_DIR / story["story_id"]
    safe_name = re.sub(r'[^\w]', '-', story['story_title'].lower())[:30]
    zip_name  = f"{safe_name}-33-chuong.zip"
    zip_path  = HOAN_THANH_DIR / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(story_dir.glob("*.txt")):
            zf.write(f, f"{story['story_title']}/{f.name}")

    print(f"   📦 Đã nén: hoan-thanh/{zip_name}")
    return zip_path


def cleanup_current_story(story: dict):
    """Xóa sạch thư mục truyện đã hoàn thành."""
    import shutil
    story_dir = DAI_DIR / story["story_id"]
    if story_dir.exists():
        shutil.rmtree(story_dir)

    # Xóa truyện ngắn cũ
    if NGAN_DIR.exists():
        shutil.rmtree(NGAN_DIR)
        NGAN_DIR.mkdir()

    print("   🧹 Đã xóa sạch dữ liệu bộ cũ")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🕯️  === TRUYỆN MA AUTO === 🕯️")
    print(f"⏰  {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

    DAI_DIR.mkdir(parents=True, exist_ok=True)
    NGAN_DIR.mkdir(parents=True, exist_ok=True)
    HOAN_THANH_DIR.mkdir(exist_ok=True)

    state       = load_state()
    today       = datetime.datetime.now()
    day_of_week = today.weekday()  # 0=Mon 6=Sun

    # ── Lấy hoặc tạo bộ truyện ──────────────────────────────────────────────
    if not state.get("story"):
        print("📚 Chưa có bộ truyện — bắt đầu research...")
        story = research_and_design_story()
        state["story"]           = story
        state["current_chapter"] = 0
        save_state(state)
    else:
        story = state["story"]

    chapter_num = state["current_chapter"] + 1

    print(f"📖 [{story['story_title']}] Chương {chapter_num}/{TOTAL_CHAPTERS}")

    # ── Research trend hôm nay ───────────────────────────────────────────────
    daily_trend  = research_daily_trend()
    prev_summary = get_prev_summary(story["story_id"], chapter_num)

    # ── Bước 1: Gemini viết thô ──────────────────────────────────────────────
    print("   ✍️  Gemini viết thô...")
    is_last = (chapter_num == TOTAL_CHAPTERS)
    raw     = call_gemini(
        prompt_write_chapter(story, chapter_num, prev_summary, daily_trend)
    )

    # ── Bước 2: Groq polish ──────────────────────────────────────────────────
    print("   ✨ Groq polish...")
    polished = call_groq(prompt_polish(raw))

    # ── Bước 3: Gemini kiểm tra ending/cliffhanger ───────────────────────────
    print("   🔪 Gemini kiểm tra cliffhanger...")
    final = call_gemini(prompt_check_ending(polished, is_last))

    # ── Lưu chương ──────────────────────────────────────────────────────────
    save_chapter(story["story_id"], chapter_num, story["story_title"], final)
    state["current_chapter"] = chapter_num
    save_state(state)

    # ── Hết 33 chương? ───────────────────────────────────────────────────────
    if is_last:
        print(f"\n🎉 Hoàn thành bộ '{story['story_title']}' ({TOTAL_CHAPTERS} chương)!")
        zip_and_archive(story)
        cleanup_current_story(story)

        # Research bộ mới
        print("\n🔍 Research bộ truyện mới...")
        new_story = research_and_design_story()
        state["story"]           = new_story
        state["current_chapter"] = 0
        save_state(state)
        print(f"✅ Bộ mới: {new_story['story_title']}")

    # ── Truyện ngắn: Thứ 4 (2) và Chủ nhật (6) ──────────────────────────────
    if day_of_week in [2, 6]:
        print("\n📝 Tạo truyện ngắn...")
        title, concept = research_short_story_theme()

        # Tránh trùng chủ đề
        used = state.get("used_short_themes", [])
        if title in used:
            title = f"{title} (Phần 2)"

        raw_short      = call_gemini(prompt_short_story(title, concept, daily_trend))
        polished_short = call_groq(prompt_polish(raw_short))
        save_short_story(title, polished_short)

        state["used_short_themes"] = used + [title]
        save_state(state)

    print("\n✅ Hoàn tất! Kiểm tra thư mục truyen/ trong repo.\n")


if __name__ == "__main__":
    main()

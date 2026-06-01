"""
Hệ thống tự động tạo truyện ma/kinh dị
─────────────────────────────────────────
Tối ưu: chỉ 2 lần gọi Gemini + 1 Groq mỗi ngày
- DuckDuckGo search (không cần key, không timeout)
- Gemini: viết chương (1 lần duy nhất)
- Groq: polish + kiểm tra cliffhanger (gộp 1 lần)
"""

import os, re, json, zipfile, random, datetime, time, requests, shutil
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
DAI_DIR        = Path("truyen/dai")
NGAN_DIR       = Path("truyen/ngan")
HOAN_THANH_DIR = Path("hoan-thanh")
STATE_FILE     = Path("truyen/state.json")

MAX_RETRIES  = 3
RETRY_WAIT   = 45   # giây chờ khi 429

# ─── AI CALLS ─────────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str:
    """Gọi Gemini — KHÔNG dùng google_search để tránh timeout."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.92, "maxOutputTokens": 3000},
    }
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(GEMINI_URL, json=payload, timeout=60)
            if r.status_code == 429:
                wait = RETRY_WAIT * (attempt + 1)
                print(f"   ⏳ Gemini 429, chờ {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            return " ".join(p.get("text","") for p in parts if "text" in p).strip()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"   ⚠️ Gemini lỗi: {e}, thử lại...")
                time.sleep(RETRY_WAIT)
            else:
                raise
    raise RuntimeError("Gemini thất bại")


def call_groq(prompt: str) -> str:
    """Gọi Groq — nhanh, ít bị rate limit."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": 3000,
    }
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
            if r.status_code == 429:
                wait = RETRY_WAIT * (attempt + 1)
                print(f"   ⏳ Groq 429, chờ {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"   ⚠️ Groq lỗi: {e}, thử lại...")
                time.sleep(RETRY_WAIT)
            else:
                raise
    raise RuntimeError("Groq thất bại")

# ─── DUCKDUCKGO SEARCH (thay thế google_search) ───────────────────────────────

def ddg_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo Instant Answer API — miễn phí, nhanh, không cần key."""
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data     = r.json()
        results  = []

        # Abstract (tóm tắt chính)
        if data.get("Abstract"):
            results.append(data["Abstract"])

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])

        return " | ".join(results[:max_results]) if results else ""
    except Exception as e:
        print(f"   ⚠️ DuckDuckGo lỗi: {e}")
        return ""

# ─── STATE ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"current_chapter": 0, "story": None, "character_bible": None,
            "plot_threads": [], "used_short_themes": []}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

# ─── RESEARCH & DESIGN ────────────────────────────────────────────────────────

def research_and_design_story() -> dict:
    """DuckDuckGo search trend → Gemini thiết kế bộ truyện."""
    print("🔍 DuckDuckGo search trend truyện ma VN...")

    # Search nhanh bằng DuckDuckGo
    trend_raw = ddg_search("truyện ma kinh dị Việt Nam 2026 đọc nhiều")
    trend_raw += " " + ddg_search("horror story Vietnam Facebook viral 2026")

    # Gemini thiết kế dựa trên kết quả search
    prompt = f"""Dựa trên xu hướng truyện ma Việt Nam hiện tại:
{trend_raw[:800] if trend_raw else "Truyện ma dân gian, tâm linh, làng quê bí ẩn đang rất hot"}

Hãy thiết kế một bộ truyện ma/kinh dị PHÙ HỢP TREND, độc đáo, chưa ai viết.
Chỉ trả về JSON (không giải thích, không markdown):
{{
  "story_id": "ten-khong-dau-gach-ngang",
  "story_title": "Tên Bộ Truyện",
  "genre": "Thể loại cụ thể",
  "setting": "Bối cảnh chi tiết, cụ thể, có hồn",
  "protagonist": "Tên — nghề nghiệp đặc biệt, đặc điểm nổi bật",
  "mystery": "Bí ẩn cốt lõi xuyên suốt 33 chương",
  "tone": "Phong cách và không khí",
  "chapter_outline": [
    "Chương 1-11: hướng đi chính",
    "Chương 12-22: leo thang và twist",
    "Chương 23-33: hé lộ và kết thúc mở"
  ]
}}"""

    raw = call_gemini(prompt)
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            story = json.loads(match.group())
            print(f"✅ Bộ truyện mới: {story.get('story_title')}")
            return story
    except Exception as e:
        print(f"⚠️ Parse lỗi: {e}")

    # Fallback
    month = datetime.datetime.now().strftime("%Y%m")
    return {
        "story_id": f"bong-toi-{month}",
        "story_title": "Bóng Tối Cuối Làng",
        "genre": "Gothic Horror",
        "setting": "Làng miền Bắc Việt Nam 1990s, người dân không ra ngoài sau 10 giờ đêm",
        "protagonist": "Minh — cựu cảnh sát 32 tuổi, trở về quê với bí mật không dám kể",
        "mystery": "Mỗi trăng tròn một đứa trẻ mất tích, liên quan ngôi miếu cổ bị phá 30 năm trước",
        "tone": "Chậm rãi, ám ảnh, từng lớp sợ hãi",
        "chapter_outline": [
            "Chương 1-11: Bối cảnh, nhân vật, gieo bí ẩn đầu tiên",
            "Chương 12-22: Bí ẩn mở rộng, twist lớn đầu tiên",
            "Chương 23-33: Sự thật hé lộ, kết thúc mở ám ảnh"
        ]
    }


def build_character_bible(story: dict) -> dict:
    """Gemini tạo character bible — chỉ gọi 1 lần khi bắt đầu bộ mới."""
    print("👤 Tạo character bible...")
    prompt = f"""Tạo CHARACTER BIBLE cho bộ truyện "{story['story_title']}".
Nhân vật: {story.get('protagonist','')}
Bí ẩn: {story.get('mystery','')}

Chỉ trả về JSON (không giải thích):
{{
  "name": "Tên đầy đủ",
  "age": "Tuổi",
  "appearance": "2-3 đặc điểm ngoại hình nổi bật, xuất hiện nhiều lần",
  "personality": "3 từ khóa tính cách cốt lõi",
  "speech_style": "Cách nói đặc trưng",
  "core_fear": "Nỗi sợ sâu nhất",
  "fatal_flaw": "Điểm yếu chí mạng",
  "character_arc": "Hành trình thay đổi từ ch.1 đến ch.33",
  "recurring_habits": ["thói quen 1", "thói quen 2"],
  "hidden_secret": "Bí mật hé lộ dần"
}}"""
    raw = call_gemini(prompt)
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            bible = json.loads(match.group())
            print(f"✅ Character: {bible.get('name')}")
            return bible
    except Exception:
        pass
    return {
        "name": story.get("protagonist","Nhân vật").split("—")[0].strip(),
        "age": "30", "appearance": "Ánh mắt sắc, vết sẹo cằm, áo tối màu",
        "personality": "Lạnh lùng — cô độc — kiên định",
        "speech_style": "Ít nói, câu ngắn, quan sát nhiều",
        "core_fear": "Sợ mất kiểm soát và lặp lại quá khứ",
        "fatal_flaw": "Quá tin lý trí, bỏ qua trực giác",
        "character_arc": "Chạy trốn quá khứ → đối mặt → chấp nhận không có đáp án",
        "recurring_habits": ["nhìn đồng hồ khi căng thẳng", "ngửi không khí trước vào phòng lạ"],
        "hidden_secret": "Biết sự thật từ đầu nhưng không dám nhìn nhận"
    }


def get_daily_trend() -> str:
    """DuckDuckGo search trend VN hôm nay — nhanh, không timeout."""
    print("📰 Search trend hôm nay...")
    queries = [
        "Việt Nam tin tức hôm nay văn hóa đời sống",
        "Vietnam trending topic today culture"
    ]
    results = []
    for q in queries:
        r = ddg_search(q, max_results=3)
        if r:
            results.append(r)

    if results:
        combined = " ".join(results)[:400]
        print(f"   ✓ Có trend: {combined[:80]}...")
        return combined
    return "Không khí xã hội bình thường, cuộc sống thường nhật với những lo toan nhỏ nhặt"

# ─── PROMPTS ──────────────────────────────────────────────────────────────────

def build_chapter_prompt(story: dict, chapter_num: int, prev_summary: str,
                          daily_trend: str, char_bible: dict,
                          plot_threads: list) -> str:

    # Arc hiện tại
    outlines = story.get("chapter_outline", ["","",""])
    if chapter_num <= 11:   arc = outlines[0]
    elif chapter_num <= 22: arc = outlines[1]
    else:                   arc = outlines[2]

    # Ending instruction
    is_last     = chapter_num == TOTAL_CHAPTERS
    is_near_end = chapter_num >= TOTAL_CHAPTERS - 3

    if is_last:
        ending = """
⚠️ CHƯƠNG CUỐI (33/33):
- Giải quyết bí ẩn theo cách bất ngờ nhất — thỏa mãn nhưng không trọn vẹn
- Twist nhỏ cuối gợi câu hỏi không có lời giải
- Câu kết: ngắn, lạnh, để người đọc tự điền
- KHÔNG cliffhanger — chỉ dư âm ám ảnh
- Thêm cuối truyện (giữ nguyên format):
---
*Ghi chú của tác giả: Câu chuyện lấy cảm hứng từ truyền thuyết dân gian Việt Nam. Một số chi tiết đã thay đổi. Một số thì không.*
---"""
    elif is_near_end:
        ending = f"⚠️ Chương {chapter_num}/33 — hồi kết: tăng kịch tính tối đa, cliffhanger MẠNH NHẤT từ đầu truyện"
    else:
        ending = "Cuối chương: cliffhanger cắt đứt đúng lúc căng nhất, không giải thích, người đọc KHÔNG THỂ bỏ qua"

    # Character bible section
    cb = char_bible or {}
    bible_txt = f"""
📋 NHÂN VẬT CHÍNH (BẤT BIẾN xuyên 33 chương):
• Tên: {cb.get('name','')} | Tuổi: {cb.get('age','')}
• Ngoại hình: {cb.get('appearance','')}
• Tính cách: {cb.get('personality','')} | Nói: {cb.get('speech_style','')}
• Nỗi sợ: {cb.get('core_fear','')} | Điểm yếu: {cb.get('fatal_flaw','')}
• Thói quen: {', '.join(cb.get('recurring_habits',[]))}
• Hành trình: {cb.get('character_arc','')}
⚠️ KHÔNG thay đổi tính cách, cách nói, thói quen của nhân vật!"""

    # Plot threads
    threads_txt = ""
    if plot_threads:
        threads_txt = "\n🧵 SỢI CHỈ CHƯA GIẢI QUYẾT (đừng mâu thuẫn):\n" + \
                      "\n".join(f"• {t}" for t in plot_threads)

    return f"""Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.

📚 "{story['story_title']}" — Chương {chapter_num}/{TOTAL_CHAPTERS}
🎭 {story.get('genre','')} | 📌 {story.get('setting','')}
🔍 BÍ ẨN: {story.get('mystery','')}
📖 ARC: {arc}
{bible_txt}
{threads_txt}

📝 {'CHƯƠNG ĐẦU — xây dựng bối cảnh rùng rợn, giới thiệu nhân vật, gieo bí ẩn đầu tiên' if chapter_num == 1 else 'CHƯƠNG TRƯỚC: ' + prev_summary}

🌐 KHÔNG KHÍ XÃ HỘI (lồng ghép ẩn dụ, không nhắc tên sự kiện):
{daily_trend[:300]}

VIẾT CHƯƠNG {chapter_num} (~2000 từ tiếng Việt):
• Harry Potter: thế giới bí ẩn có chiều sâu, chi tiết sống động kích thích giác quan
• Dan Brown: nhịp nhanh, tiết lộ từng giọt, câu cuối mỗi đoạn là hook
• Sợ hãi xây dựng từ từ — cái không thấy đáng sợ hơn cái thấy
• Tránh clichés: không ma la hét, không nhân vật ngốc vô lý
• {ending}

Viết ngay:"""


def build_polish_prompt(raw: str, is_last: bool) -> str:
    """Groq vừa polish VĂN PHONG vừa kiểm tra CLIFFHANGER — 1 lần duy nhất."""
    ending_check = (
        "Đảm bảo kết thúc mở: câu kết ngắn, lạnh, ám ảnh. Giữ ghi chú tác giả cuối."
        if is_last else
        "Đảm bảo cliffhanger cuối ĐỦ MẠNH — nếu yếu, viết lại 3-4 câu cuối cho sắc bén hơn."
    )
    return f"""Bạn là editor + tác giả kinh dị kỳ cựu. Làm 2 việc cùng lúc:

1. POLISH văn phong:
   - Câu chảy, nhịp điệu, đọc cuốn không dứt
   - Tăng chi tiết cảm giác (âm thanh, mùi, xúc giác, nhiệt độ)
   - Xóa câu thừa, từ lặp

2. KIỂM TRA ENDING: {ending_check}

KHÔNG thay đổi cốt truyện, nhân vật, ghi chú tác giả.
Chỉ trả về văn bản hoàn chỉnh:

{raw}"""


def build_short_story_prompt(title: str, concept: str, trend: str) -> str:
    return f"""Viết truyện ngắn kinh dị hoàn chỉnh bằng tiếng Việt (~1300 từ):

Tên: "{title}"
Ý tưởng: {concept}
Không khí xã hội (ẩn dụ tinh tế): {trend[:200]}

Cấu trúc: mở đầu ám ảnh → xây dựng → cao trào → twist kết bất ngờ
Câu kết: lạnh gáy, ngắn, để người đọc tự cảm nhận.
Viết ngay:"""

# ─── FILE OPS ─────────────────────────────────────────────────────────────────

def get_prev_summary(story_id: str, chapter_num: int) -> str:
    if chapter_num <= 1:
        return ""
    f = DAI_DIR / story_id / f"chuong-{chapter_num-1:03d}.txt"
    if f.exists():
        lines = f.read_text(encoding="utf-8").split("\n")
        body  = "\n".join(lines[6:])
        return body[:600] + "..." if len(body) > 600 else body
    return ""

def save_chapter(story_id: str, chapter_num: int, title: str, content: str):
    d = DAI_DIR / story_id
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now().strftime("%d/%m/%Y")
    f   = d / f"chuong-{chapter_num:03d}.txt"
    f.write_text(
        f"{'='*60}\n{title}\nChương {chapter_num}/{TOTAL_CHAPTERS}\n{now}\n{'='*60}\n\n{content}",
        encoding="utf-8"
    )
    print(f"   💾 {f.name}")

def save_short(title: str, content: str):
    NGAN_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    safe = re.sub(r'[^\w]', '-', title.lower())[:40]
    f    = NGAN_DIR / f"{date}-{safe}.txt"
    now  = datetime.datetime.now().strftime("%d/%m/%Y")
    f.write_text(
        f"{'='*60}\nTRUYỆN NGẮN: {title}\n{now}\n{'='*60}\n\n{content}",
        encoding="utf-8"
    )
    print(f"   💾 {f.name}")

def zip_story(story: dict):
    HOAN_THANH_DIR.mkdir(exist_ok=True)
    safe     = re.sub(r'[^\w]', '-', story['story_title'].lower())[:30]
    zip_path = HOAN_THANH_DIR / f"{safe}-33-chuong.zip"
    story_dir = DAI_DIR / story["story_id"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(story_dir.glob("*.txt")):
            zf.write(f, f"{story['story_title']}/{f.name}")
    print(f"   📦 hoan-thanh/{zip_path.name}")

def cleanup(story: dict):
    d = DAI_DIR / story["story_id"]
    if d.exists():
        shutil.rmtree(d)
    if NGAN_DIR.exists():
        shutil.rmtree(NGAN_DIR)
        NGAN_DIR.mkdir()
    print("   🧹 Đã xóa sạch")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n🕯️  TRUYỆN MA AUTO — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

    DAI_DIR.mkdir(parents=True, exist_ok=True)
    NGAN_DIR.mkdir(parents=True, exist_ok=True)
    HOAN_THANH_DIR.mkdir(exist_ok=True)

    state       = load_state()
    today       = datetime.datetime.now()
    day_of_week = today.weekday()

    # ── Khởi tạo bộ truyện nếu chưa có ─────────────────────────────────────
    if not state.get("story"):
        print("📚 Research & thiết kế bộ truyện mới...")
        story = research_and_design_story()
        # Delay giữa 2 lần gọi Gemini
        time.sleep(10)
        bible = build_character_bible(story)
        state.update({"story": story, "character_bible": bible,
                      "current_chapter": 0, "plot_threads": []})
        save_state(state)
    else:
        story = state["story"]
        bible = state.get("character_bible") or {}

    chapter_num  = state["current_chapter"] + 1
    plot_threads = state.get("plot_threads", [])

    print(f"📖 [{story['story_title']}] Chương {chapter_num}/{TOTAL_CHAPTERS}")

    # ── Search trend (nhanh, DuckDuckGo) ────────────────────────────────────
    daily_trend  = get_daily_trend()
    prev_summary = get_prev_summary(story["story_id"], chapter_num)

    # ── Bước 1: Gemini viết chương (1 lần duy nhất) ─────────────────────────
    print("   ✍️  Gemini viết chương...")
    is_last = chapter_num == TOTAL_CHAPTERS
    raw     = call_gemini(
        build_chapter_prompt(story, chapter_num, prev_summary,
                             daily_trend, bible, plot_threads)
    )
    time.sleep(8)  # Delay nhỏ giữa Gemini và Groq

    # ── Bước 2: Groq polish + check cliffhanger (gộp 1 lần) ────────────────
    print("   ✨ Groq polish & cliffhanger...")
    final = call_groq(build_polish_prompt(raw, is_last))

    # ── Lưu chương ──────────────────────────────────────────────────────────
    save_chapter(story["story_id"], chapter_num, story["story_title"], final)

    # Cập nhật plot threads đơn giản (không gọi AI thêm)
    if len(plot_threads) < 6:
        # Tự thêm placeholder — không tốn API call
        plot_threads.append(f"Bí ẩn chương {chapter_num} chưa giải quyết")
        plot_threads = plot_threads[-6:]  # Giữ tối đa 6

    state["current_chapter"] = chapter_num
    state["plot_threads"]     = plot_threads
    save_state(state)
    print(f"   ✅ Xong chương {chapter_num}")

    # ── Hết 33 chương ───────────────────────────────────────────────────────
    if is_last:
        print(f"\n🎉 Hoàn thành '{story['story_title']}'!")
        zip_story(story)
        cleanup(story)

        print("🔍 Research bộ truyện mới...")
        time.sleep(10)
        new_story = research_and_design_story()
        time.sleep(10)
        new_bible = build_character_bible(new_story)
        state.update({"story": new_story, "character_bible": new_bible,
                      "current_chapter": 0, "plot_threads": []})
        save_state(state)
        print(f"✅ Bộ mới: {new_story['story_title']}")

    # ── Truyện ngắn: Thứ 4 + CN ─────────────────────────────────────────────
    if day_of_week in [2, 6]:
        print("\n📝 Tạo truyện ngắn...")

        # Chủ đề có sẵn — không cần gọi AI thêm
        themes = [
            ("Gương Không Phản Chiếu", "Chiếc gương cổ phản chiếu thứ không có trong phòng — tối nay nó hiện một khuôn mặt không phải của bạn"),
            ("3:33 Sáng", "Mỗi đêm 3:33, điện thoại tự bật hiện ảnh phòng ngủ từ góc không có camera"),
            ("Nhật Ký Ngày Mai", "Cuốn nhật ký viết chuyện sẽ xảy ra từ ngày mai — trang cuối viết về cái chết của người tìm thấy nó"),
            ("Tiếng Bước Chân Tầng Trên", "Căn hộ tầng trên bỏ trống 3 năm, mỗi đêm vẫn có 12 bước chân rồi dừng đúng chỗ"),
            ("Người Thứ Tám", "Ảnh gia đình 7 người nhưng in ra luôn thêm người thứ 8 — khuôn mặt mỗi lần một khác"),
            ("Số Điện Thoại Của Mẹ", "Mẹ mất 2 năm. Hôm nay số mẹ gọi đến và nói: con đừng về nhà tối nay"),
            ("Đứa Trẻ Trong Tủ", "Con gái 4 tuổi nói chuyện với bạn trong tủ mỗi tối. Hôm nay nó nói bạn ấy muốn ra ngoài"),
            ("Căn Phòng 404", "Khách sạn 3 tầng nhưng thang máy có nút tầng 4. Một lần bạn bấm nhầm"),
            ("Bức Tranh Thay Đổi", "Tranh phong cảnh treo 20 năm. Hôm nay có thêm bóng người đứng trong tranh"),
            ("Giếng Cổ", "Người ta bịt giếng vì nghe tiếng gõ từ dưới lên. Hôm nay nắp giếng bị mở từ bên trong"),
            ("Kẻ Đứng Ngoài Cửa Sổ", "Camera ghi bóng người đứng nhìn cửa sổ phòng ngủ bạn mỗi đêm — từ tầng 12"),
            ("Con Búp Bê Cũ", "Búp bê bà ngoại để lại, mắt luôn nhìn theo. Đêm qua để nó quay vào tường. Sáng ra nó đang nhìn bạn"),
        ]

        used  = state.get("used_short_themes", [])
        avail = [(t,c) for t,c in themes if t not in used]
        if not avail:
            avail = themes
            state["used_short_themes"] = []

        title, concept = random.choice(avail)
        time.sleep(8)  # Delay trước khi gọi Gemini lần 2

        raw_s   = call_gemini(build_short_story_prompt(title, concept, daily_trend))
        time.sleep(5)
        final_s = call_groq(build_polish_prompt(raw_s, False))
        save_short(title, final_s)

        state["used_short_themes"] = used + [title]
        save_state(state)
        print(f"   ✅ Truyện ngắn: {title}")

    print("\n✅ Hoàn tất! Xem truyen/ trong repo.\n")

if __name__ == "__main__":
    main()

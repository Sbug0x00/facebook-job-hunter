"""
Hệ thống tự động tạo truyện ma/kinh dị
─────────────────────────────────────────
- Gemini: chỉ design story + character bible (1 lần / 33 ngày)
- Groq (Llama 3.3 70B): viết chương mỗi ngày — ổn định, không 429
- DuckDuckGo: search trend (không cần key)
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

# ─── AI CALLS ─────────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str:
    """Chỉ dùng cho design story — gọi tối đa 2 lần mỗi 33 ngày."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000},
    }
    for attempt in range(3):
        try:
            r = requests.post(GEMINI_URL, json=payload, timeout=60)
            if r.status_code == 429:
                print(f"   ⏳ Gemini 429, chờ 65s (lần {attempt+1})...")
                time.sleep(65)
                continue
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            return " ".join(p.get("text","") for p in parts if "text" in p).strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(30)
            else:
                raise
    raise RuntimeError("Gemini thất bại")


def call_groq(prompt: str, max_tokens: int = 3500) -> str:
    """Dùng cho mọi việc viết chương — ổn định, không 429."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.88,
        "max_tokens": max_tokens,
    }
    for attempt in range(3):
        try:
            r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=90)
            if r.status_code == 429:
                print(f"   ⏳ Groq 429, chờ 30s (lần {attempt+1})...")
                time.sleep(30)
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(15)
            else:
                raise
    raise RuntimeError("Groq thất bại")

# ─── DUCKDUCKGO SEARCH ────────────────────────────────────────────────────────

def ddg_search(query: str, max_results: int = 4) -> str:
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data    = r.json()
        results = []
        if data.get("Abstract"):
            results.append(data["Abstract"])
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])
        return " | ".join(results) if results else ""
    except Exception:
        return ""

# ─── STATE ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "current_chapter": 0,
        "story": None,
        "character_bible": None,
        "plot_threads": [],
        "used_short_themes": [],
    }

def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# ─── DESIGN STORY (Gemini — 1 lần / 33 ngày) ─────────────────────────────────

def design_new_story() -> tuple:
    """Gemini research trend + thiết kế bộ truyện + character bible."""
    print("🔍 Search trend...")
    trend = ddg_search("truyện ma kinh dị Việt Nam 2026 viral")
    trend += " " + ddg_search("horror story Vietnam Facebook trending")

    print("🎨 Gemini thiết kế bộ truyện...")
    story_prompt = f"""Xu hướng truyện ma Việt Nam hiện tại: {trend[:600] or "tâm linh dân gian, làng quê bí ẩn, nhân vật có năng lực đặc biệt"}

Thiết kế một bộ truyện ma/kinh dị Việt Nam PHÙ HỢP TREND, độc đáo.
Chỉ trả về JSON (không markdown, không giải thích):
{{
  "story_id": "ten-khong-dau-gach-ngang",
  "story_title": "Tên Bộ Truyện",
  "genre": "Thể loại",
  "setting": "Bối cảnh chi tiết, cụ thể",
  "protagonist": "Tên — nghề nghiệp đặc biệt, đặc điểm",
  "mystery": "Bí ẩn cốt lõi xuyên suốt 33 chương",
  "tone": "Phong cách và không khí",
  "arc_1": "Hướng chương 1-11",
  "arc_2": "Hướng chương 12-22",
  "arc_3": "Hướng chương 23-33"
}}"""

    raw = call_gemini(story_prompt)
    story = None
    try:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            story = json.loads(match.group())
            print(f"✅ Bộ truyện: {story.get('story_title')}")
    except Exception:
        pass

    if not story:
        month = datetime.datetime.now().strftime("%Y%m")
        story = {
            "story_id": f"bong-toi-{month}",
            "story_title": "Bóng Tối Cuối Làng",
            "genre": "Gothic Horror",
            "setting": "Làng miền Bắc Việt Nam 1990s, không ai ra ngoài sau 10 giờ đêm",
            "protagonist": "Minh — cựu cảnh sát 32 tuổi, trở về quê với bí mật chôn vùi",
            "mystery": "Mỗi trăng tròn một đứa trẻ mất tích, liên quan ngôi miếu cổ bị phá 30 năm trước",
            "tone": "Chậm rãi, ám ảnh, từng lớp sợ hãi xây dựng đến vỡ òa",
            "arc_1": "Xây dựng bối cảnh rùng rợn, giới thiệu nhân vật, gieo bí ẩn đầu tiên",
            "arc_2": "Bí ẩn mở rộng, twist lớn đầu tiên, nhân vật đối mặt hiểm nguy",
            "arc_3": "Sự thật hé lộ từng mảnh, cao trào, kết thúc mở ám ảnh"
        }

    # Character bible — cũng dùng Gemini (cùng lần / 33 ngày)
    print("👤 Gemini tạo character bible...")
    time.sleep(65)  # Chờ quota/phút reset trước lần gọi Gemini thứ 2

    bible_prompt = f"""Tạo CHARACTER BIBLE cho bộ truyện "{story['story_title']}".
Nhân vật: {story.get('protagonist','')}
Bối cảnh: {story.get('setting','')}

Chỉ trả về JSON (không markdown):
{{
  "name": "Tên đầy đủ",
  "age": "Tuổi",
  "appearance": "2-3 đặc điểm ngoại hình xuất hiện xuyên suốt",
  "personality": "3 từ khóa tính cách cốt lõi",
  "speech_style": "Cách nói đặc trưng",
  "core_fear": "Nỗi sợ sâu nhất",
  "fatal_flaw": "Điểm yếu chí mạng",
  "character_arc": "Hành trình từ ch.1 đến ch.33",
  "recurring_habits": ["thói quen 1", "thói quen 2"],
  "hidden_secret": "Bí mật hé lộ dần"
}}"""

    raw_bible = call_gemini(bible_prompt)
    bible = None
    try:
        match = re.search(r'\{[\s\S]*\}', raw_bible)
        if match:
            bible = json.loads(match.group())
            print(f"✅ Nhân vật: {bible.get('name')}")
    except Exception:
        pass

    if not bible:
        name = story.get("protagonist","Nhân vật").split("—")[0].strip()
        bible = {
            "name": name, "age": "30",
            "appearance": "Ánh mắt sắc bén, vết sẹo nhỏ ở cằm, hay mặc áo tối màu",
            "personality": "Lạnh lùng — cô độc — kiên định",
            "speech_style": "Ít nói, câu ngắn, quan sát nhiều hơn phát biểu",
            "core_fear": "Sợ mất kiểm soát và lặp lại sai lầm quá khứ",
            "fatal_flaw": "Quá tin lý trí, bỏ qua trực giác đến khi quá muộn",
            "character_arc": "Từ người chạy trốn quá khứ → đối mặt sự thật → chấp nhận không có đáp án",
            "recurring_habits": ["nhìn đồng hồ khi căng thẳng", "ngửi không khí trước khi vào phòng lạ"],
            "hidden_secret": "Biết sự thật từ đầu nhưng không dám thừa nhận với chính mình"
        }

    return story, bible

# ─── DAILY TREND ──────────────────────────────────────────────────────────────

def get_daily_trend() -> str:
    print("📰 Search trend hôm nay...")
    r1 = ddg_search("Việt Nam tin tức văn hóa đời sống hôm nay")
    r2 = ddg_search("Vietnam news culture lifestyle today")
    result = (r1 + " " + r2).strip()[:400]
    if result:
        print(f"   ✓ {result[:80]}...")
        return result
    return "Cuộc sống thường nhật với những lo toan ngầm chảy bên dưới bề mặt yên bình"

# ─── PROMPTS (Groq viết chương) ───────────────────────────────────────────────

def build_chapter_prompt(story: dict, chapter_num: int, prev_summary: str,
                          trend: str, bible: dict, threads: list) -> str:
    # Arc
    if chapter_num <= 11:   arc = story.get("arc_1","")
    elif chapter_num <= 22: arc = story.get("arc_2","")
    else:                   arc = story.get("arc_3","")

    is_last     = chapter_num == TOTAL_CHAPTERS
    is_near_end = chapter_num >= TOTAL_CHAPTERS - 3

    if is_last:
        ending = """
⚠️ CHƯƠNG CUỐI (33/33) — KẾT THÚC MỞ:
- Giải quyết bí ẩn theo cách bất ngờ nhất — thỏa mãn nhưng không trọn vẹn
- Twist nhỏ cuối gợi câu hỏi không có lời giải
- Câu kết: ngắn, lạnh, để người đọc tự điền khoảng trống
- KHÔNG cliffhanger — chỉ dư âm ám ảnh
- Thêm đúng đoạn này vào cuối (giữ nguyên):

---
*Ghi chú của tác giả: Câu chuyện lấy cảm hứng từ truyền thuyết dân gian Việt Nam. Một số chi tiết đã thay đổi. Một số thì không.*
---"""
    elif is_near_end:
        ending = f"⚠️ Chương {chapter_num}/33 — hồi kết: tăng kịch tính tối đa, cliffhanger MẠNH NHẤT từ đầu truyện"
    else:
        ending = "Cuối chương: cliffhanger cắt đứt đúng lúc căng nhất — người đọc KHÔNG THỂ bỏ qua chương tiếp"

    cb = bible or {}
    bible_txt = f"""
📋 NHÂN VẬT CHÍNH (BẤT BIẾN xuyên 33 chương — KHÔNG ĐƯỢC thay đổi):
• Tên: {cb.get('name','')} | Tuổi: {cb.get('age','')}
• Ngoại hình: {cb.get('appearance','')}
• Tính cách: {cb.get('personality','')}
• Cách nói: {cb.get('speech_style','')}
• Nỗi sợ: {cb.get('core_fear','')}
• Điểm yếu: {cb.get('fatal_flaw','')}
• Thói quen: {', '.join(cb.get('recurring_habits',[]))}
• Hành trình: {cb.get('character_arc','')}"""

    threads_txt = ""
    if threads:
        threads_txt = "\n🧵 SỢI CHỈ CHƯA GIẢI QUYẾT:\n" + "\n".join(f"• {t}" for t in threads[-5:])

    return f"""Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.

📚 "{story['story_title']}" — Chương {chapter_num}/{TOTAL_CHAPTERS}
🎭 {story.get('genre','')} | 📌 {story.get('setting','')}
🔍 BÍ ẨN: {story.get('mystery','')}
📖 ARC HIỆN TẠI: {arc}
{bible_txt}
{threads_txt}

📝 {'CHƯƠNG ĐẦU TIÊN — xây dựng bối cảnh rùng rợn, giới thiệu nhân vật sâu sắc, gieo bí ẩn đầu tiên khiến người đọc tò mò ngay dòng đầu' if chapter_num == 1 else 'CHƯƠNG TRƯỚC: ' + prev_summary}

🌐 KHÔNG KHÍ XÃ HỘI HÔM NAY (lồng ghép ẩn dụ tinh tế, không nhắc tên sự kiện):
{trend[:250]}

VIẾT CHƯƠNG {chapter_num} (~2000 từ tiếng Việt):
• Phong cách Harry Potter: thế giới bí ẩn sâu sắc, chi tiết kích thích giác quan
• Phong cách Dan Brown: nhịp nhanh, tiết lộ từng giọt, câu cuối mỗi đoạn là hook
• Sợ hãi xây dựng từ từ — cái không thấy đáng sợ hơn cái thấy
• Mỗi chương tiết lộ ÍT NHẤT 1 chi tiết mới thay đổi cách hiểu của người đọc
• {ending}

Viết ngay, không cần lời dẫn:"""


def build_polish_prompt(raw: str, is_last: bool) -> str:
    ending_check = (
        "Đảm bảo kết thúc mở: câu kết ngắn, lạnh, ám ảnh. Giữ nguyên ghi chú tác giả cuối."
        if is_last else
        "Đảm bảo cliffhanger cuối đủ mạnh — nếu yếu, viết lại 3-4 câu cuối sắc bén hơn."
    )
    return f"""Bạn là editor truyện kinh dị chuyên nghiệp. Làm 2 việc:

1. POLISH văn phong: câu chảy, nhịp cuốn, tăng chi tiết cảm giác (âm thanh/mùi/xúc giác), xóa từ thừa
2. KIỂM TRA ENDING: {ending_check}

KHÔNG thay đổi cốt truyện, nhân vật, ghi chú tác giả.
Chỉ trả về văn bản hoàn chỉnh:

{raw}"""


def build_short_prompt(title: str, concept: str, trend: str) -> str:
    return f"""Bạn là tác giả truyện kinh dị hàng đầu Việt Nam.
Viết truyện ngắn kinh dị hoàn chỉnh (~1300 từ tiếng Việt):

Tên: "{title}"
Ý tưởng: {concept}
Không khí xã hội (ẩn dụ tinh tế, không nhắc trực tiếp): {trend[:200]}

Cấu trúc: mở đầu ám ảnh → xây dựng sợ hãi → cao trào → twist kết bất ngờ
Twist cuối làm người đọc nhìn lại toàn bộ theo ánh sáng mới.
Câu kết: lạnh gáy, ngắn, ám ảnh.
Viết ngay:"""

# ─── FILE OPS ─────────────────────────────────────────────────────────────────

def get_prev_summary(story_id: str, chapter_num: int) -> str:
    if chapter_num <= 1:
        return ""
    f = DAI_DIR / story_id / f"chuong-{chapter_num-1:03d}.txt"
    if f.exists():
        lines = f.read_text(encoding="utf-8").split("\n")
        body  = "\n".join(lines[5:])
        return body[:700] + "..." if len(body) > 700 else body
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
    now  = datetime.datetime.now().strftime("%d/%m/%Y")
    f    = NGAN_DIR / f"{date}-{safe}.txt"
    f.write_text(
        f"{'='*60}\nTRUYỆN NGẮN: {title}\n{now}\n{'='*60}\n\n{content}",
        encoding="utf-8"
    )
    print(f"   💾 {f.name}")

def zip_story(story: dict):
    HOAN_THANH_DIR.mkdir(exist_ok=True)
    safe      = re.sub(r'[^\w]', '-', story['story_title'].lower())[:30]
    zip_path  = HOAN_THANH_DIR / f"{safe}-33-chuong.zip"
    story_dir = DAI_DIR / story["story_id"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(story_dir.glob("*.txt")):
            zf.write(f, f"{story['story_title']}/{f.name}")
    print(f"   📦 hoan-thanh/{zip_path.name}")

def cleanup(story: dict):
    d = DAI_DIR / story["story_id"]
    if d.exists(): shutil.rmtree(d)
    if NGAN_DIR.exists():
        shutil.rmtree(NGAN_DIR)
        NGAN_DIR.mkdir()
    print("   🧹 Đã xóa sạch")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

SHORT_THEMES = [
    ("Gương Không Phản Chiếu", "Chiếc gương cổ phản chiếu thứ không có trong phòng — tối nay hiện khuôn mặt không phải của bạn"),
    ("3:33 Sáng", "Mỗi đêm 3:33 điện thoại tự bật hiện ảnh phòng ngủ từ góc không có camera"),
    ("Nhật Ký Ngày Mai", "Cuốn nhật ký viết chuyện sẽ xảy ra từ ngày mai — trang cuối viết về cái chết của người tìm thấy nó"),
    ("Tiếng Bước Chân Tầng Trên", "Căn hộ tầng trên bỏ trống 3 năm, mỗi đêm vẫn có đúng 12 bước chân rồi dừng"),
    ("Người Thứ Tám", "Ảnh gia đình 7 người nhưng in ra luôn thêm người thứ 8 — khuôn mặt mỗi lần một khác"),
    ("Số Điện Thoại Của Mẹ", "Mẹ mất 2 năm. Hôm nay số mẹ gọi và nói: con đừng về nhà tối nay"),
    ("Đứa Trẻ Trong Tủ", "Con gái 4 tuổi nói chuyện với bạn trong tủ mỗi tối. Hôm nay nó nói bạn ấy muốn ra ngoài"),
    ("Căn Phòng 404", "Khách sạn 3 tầng nhưng thang máy có nút tầng 4. Một lần bạn bấm nhầm"),
    ("Bức Tranh Thay Đổi", "Tranh phong cảnh treo 20 năm. Hôm nay có thêm bóng người đứng trong tranh"),
    ("Giếng Cổ", "Người ta bịt giếng vì nghe tiếng gõ từ dưới lên. Hôm nay nắp bị mở từ bên trong"),
    ("Kẻ Đứng Ngoài Cửa Sổ", "Camera ghi bóng người nhìn vào cửa sổ phòng ngủ mỗi đêm — từ tầng 12"),
    ("Con Búp Bê Cũ", "Búp bê bà ngoại để lại, mắt luôn nhìn theo. Đêm qua để quay vào tường. Sáng ra đang nhìn bạn"),
]

def main():
    print(f"\n🕯️  TRUYỆN MA AUTO — {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

    DAI_DIR.mkdir(parents=True, exist_ok=True)
    NGAN_DIR.mkdir(parents=True, exist_ok=True)
    HOAN_THANH_DIR.mkdir(exist_ok=True)

    state       = load_state()
    day_of_week = datetime.datetime.now().weekday()

    # ── Khởi tạo bộ mới nếu chưa có (Gemini chạy ở đây) ────────────────────
    if not state.get("story"):
        story, bible = design_new_story()  # Gemini: 2 lần gọi, cách nhau 65s
        state.update({
            "story": story, "character_bible": bible,
            "current_chapter": 0, "plot_threads": []
        })
        save_state(state)
    else:
        story = state["story"]
        bible = state.get("character_bible") or {}

    chapter_num = state["current_chapter"] + 1
    threads     = state.get("plot_threads", [])

    print(f"📖 [{story['story_title']}] Chương {chapter_num}/{TOTAL_CHAPTERS}")

    # ── Search trend (DuckDuckGo, nhanh) ────────────────────────────────────
    trend        = get_daily_trend()
    prev_summary = get_prev_summary(story["story_id"], chapter_num)

    # ── Groq viết chương ────────────────────────────────────────────────────
    is_last = chapter_num == TOTAL_CHAPTERS
    print("   ✍️  Groq viết chương...")
    raw = call_groq(build_chapter_prompt(
        story, chapter_num, prev_summary, trend, bible, threads
    ))

    # ── Groq polish + cliffhanger (gộp 1 lần) ───────────────────────────────
    print("   ✨ Groq polish...")
    final = call_groq(build_polish_prompt(raw, is_last))

    save_chapter(story["story_id"], chapter_num, story["story_title"], final)

    # Cập nhật plot threads
    threads.append(f"Bí ẩn từ chương {chapter_num}")
    state["current_chapter"] = chapter_num
    state["plot_threads"]    = threads[-6:]
    save_state(state)
    print(f"   ✅ Xong chương {chapter_num}")

    # ── Hết 33 chương ───────────────────────────────────────────────────────
    if is_last:
        print(f"\n🎉 Hoàn thành '{story['story_title']}'!")
        zip_story(story)
        cleanup(story)
        # Reset để lần chạy tiếp Gemini sẽ design bộ mới
        state.update({"story": None, "character_bible": None,
                      "current_chapter": 0, "plot_threads": []})
        save_state(state)
        print("🔄 Bộ mới sẽ được tạo vào ngày mai.")

    # ── Truyện ngắn: Thứ 4 (2) + Chủ nhật (6) ───────────────────────────────
    if day_of_week in [2, 6]:
        print("\n📝 Tạo truyện ngắn...")
        used  = state.get("used_short_themes", [])
        avail = [(t,c) for t,c in SHORT_THEMES if t not in used]
        if not avail:
            avail = SHORT_THEMES
            state["used_short_themes"] = []

        title, concept = random.choice(avail)
        print(f"   Chủ đề: {title}")

        raw_s   = call_groq(build_short_prompt(title, concept, trend))
        final_s = call_groq(build_polish_prompt(raw_s, False), max_tokens=2000)
        save_short(title, final_s)

        state["used_short_themes"] = used + [title]
        save_state(state)
        print(f"   ✅ Xong: {title}")

    print("\n✅ Hoàn tất!\n")

if __name__ == "__main__":
    main()

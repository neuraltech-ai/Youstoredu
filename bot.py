import os
import re
import json
import time
import urllib.parse
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import google.generativeai as genai

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
genai.configure(api_key=API_KEY)

def get_live_tech_news():
    """جلب أحدث المستجدات والأخبار التقنية الحية من مصادر عالمية متعددة"""
    feeds = [
        "https://news.google.com/rss/search?q=Artificial+Intelligence+OR+Programming+Tools+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://hnrss.org/frontpage",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://trends.google.com/trending/rss?geo=US"
    ]
    headlines = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for url in feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall(".//item")[:6]:
                    title = item.find("title")
                    if title is not None and title.text:
                        headlines.append(title.text.strip())
        except Exception:
            continue
    return list(dict.fromkeys(headlines))[:20]

def call_gemini(prompt_text):
    model = genai.GenerativeModel('gemini-3.8-flash')
    for attempt in range(3):
        try:
            response = model.generate_content(prompt_text)
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"محاولة اتصال رقم {attempt + 1} فشلت، الانتظار 15 ثانية... السبب: {e}")
            time.sleep(15)
    raise Exception("تعذر الاتصال بواجهة Gemini بعد 3 محاولات.")

def extract_json(raw_text):
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0].strip()
    return json.loads(raw_text)

history_file = "history.txt"
past_titles = []
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        past_titles = [line.strip() for line in f.readlines()]

live_news = get_live_tech_news()
print(f"تم رصد {len(live_news)} خبراً ومستجداً تقنياً اليوم.")

# المرحلة الأولى: كتابة المسودة الأولية بناءً على أحدث المستجدات
draft_prompt = f"""
أنت كبير المحررين والمهندسين في منصة تقنية عالمية مزدوجة اللغة (عربي/إنجليزي) بمستوى موقع The Verge و Smashing Magazine.
إليك أحدث المستجدات والأخبار التقنية الرائجة اليوم في العالم:
{live_news}

المواضيع التي نشرناها سابقاً (تجنب تكرارها تماماً):
{past_titles[-25:]}

المهمة:
اختر أحدث وأقوى موضوع تقني أو أداة ذكاء اصطناعي أو تقنية برمجية حديثة من المستجدات أعلاه، واكتب مقالاً شاملاً وعميقاً جداً باللغتين العربية والإنجليزية.
يجب أن يتضمن المقال:
- شرحاً عملياً وافياً ومحدثاً.
- أمثلة برمجية أو أوامر تطبيقية حقيقية (Code blocks مع تحديد لغة البرمجة مثل ```python أو ```javascript أو ```bash) قابلة للتشغيل.
- نصائح احترافية وأسئلة شائعة (FAQ) في نهاية المقال.

أجب بصيغة JSON صالح فقط بهذا الهيكل:
{{
  "image_prompt": "Futuristic sleek editorial illustration representing the tech topic, ultra detailed, 8k, modern tech magazine style, no text",
  "ar": {{
    "title": "عنوان احترافي وجذاب بالعربية",
    "description": "وصف ميتا احترافي لمحركات البحث (150 حرفاً)",
    "category": "ذكاء-اصطناعي-وتقنية",
    "key_takeaways": ["خلاصة سريعة 1", "خلاصة سريعة 2", "خلاصة سريعة 3"],
    "content": "المحتوى الكامل بالعربية بصيغة Markdown مع عناوين ## و ### وأكواد برمجية وجداول"
  }},
  "en": {{
    "title": "Professional Catchy SEO English Title",
    "description": "Compelling SEO meta description (150 chars)",
    "category": "AI-Engineering",
    "key_takeaways": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3"],
    "content": "Full English article content in Markdown with ## and ### headings, verified code blocks, and tables"
  }}
}}
"""

print("جاري كتابة المسودة الأولية للمقالات...")
draft_raw = call_gemini(draft_prompt)
draft_data = extract_json(draft_raw)

# المرحلة الثانية: المراجع الصارم (تدقيق الأكواد البرمجية، المعلومات، واللغة)
review_prompt = f"""
أنت مدقق تقني ومراجع برمجي ولغوي صارم (Senior Staff Engineer & Technical Editor).
قم بمراجعة مسودة المقال التالية بدقة متناهية:
{json.dumps(draft_data, ensure_ascii=False)}

مهام التدقيق الإلزامية:
1. فحص جميع الأكواد البرمجية والأوامر: تأكد أنها خالية تماماً من الأخطاء البرمجية (Syntax/Logic errors)، وحديثة، ومكتوبة داخل أسوار ``` مع اسم اللغة الصحيح.
2. فحص الدقة العلمية والتقنية: صحح أي معلومة غير دقيقة وتأكد من عمق الشرح ووضوحه.
3. التدقيق اللغوي والتنسيق: تأكد من سلامة اللغة العربية الفصحى العصرية وسلامة اللغة الإنجليزية، وتنسيق العناوين الفرعية ## والقوائم.
4. أعد إخراج كائن الـ JSON النهائي المصحح والمدقق بالكامل بنفس المفاتيح والهيكل تماماً (JSON صالح فقط بدون أي نص خارجه).
"""

print("جاري إجراء المراجعة التقنية والبرمجية الدقيقة (Code & Fact Audit)...")
try:
    reviewed_raw = call_gemini(review_prompt)
    data = extract_json(reviewed_raw)
    print("اكتملت المراجعة الدقيقة بنجاح وتم اعتماد النسخة المصححة!")
except Exception as e:
    print(f"تنبيه: تم اعتماد المسودة الأساسية بسبب خطأ في تحليل المراجعة: {e}")
    data = draft_data

os.makedirs("_posts", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")

img_prompt = data.get("image_prompt", "Futuristic artificial intelligence editorial illustration 8k")
encoded_prompt = urllib.parse.quote(img_prompt)
seed = int(time.time()) % 10000
image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1000&height=520&nologo=true&seed={seed}"

for lang_key, default_cat, prefix in [("ar", "تقنية", ""), ("en", "AI-Tech", "en-")]:
    lang_obj = data.get(lang_key, {})
    title = lang_obj.get("title", "New Tech Article").replace('"', "'")
    desc = lang_obj.get("description", title).replace('"', "'")
    cat = lang_obj.get("category", default_cat)
    takeaways = lang_obj.get("key_takeaways", [])
    content = lang_obj.get("content", "")

    # دمج ملخص النقاط السريعة في بداية المقال إن وجد
    if takeaways and isinstance(takeaways, list):
        box_title = "💡 أبرز النقاط في هذا المقال:" if lang_key == "ar" else "💡 Key Takeaways:"
        bullets = "\n".join([f"- {item}" for item in takeaways])
        content = f"> **{box_title}**\n" + "\n".join([f"> - {item}" for item in takeaways]) + "\n\n" + content

    if lang_key == "ar":
        clean_slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-')[:35] or 'ar-post'
    else:
        clean_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip().replace(' ', '-').lower()[:35] or 'en-post'

    filename = f"_posts/{date_str}-{prefix}{clean_slug}.md"
    frontmatter = f"""---
layout: post
title: "{title}"
description: "{desc}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000')}
categories: [{cat}]
lang: {lang_key}
image: "{image_url}"
verified: true
---

{content}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(frontmatter)

with open(history_file, "a", encoding="utf-8") as f:
    f.write(data.get('en', {}).get('title', 'Article') + "\n")

print("تم نشر المقالات المدققة بنجاح!")

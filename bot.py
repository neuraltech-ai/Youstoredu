import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import google.generativeai as genai

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
genai.configure(api_key=API_KEY)

def get_daily_trends():
    try:
        res = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=10)
        root = ET.fromstring(res.content)
        return [item.find("title").text for item in root.findall(".//item")[:10]]
    except Exception:
        return []

history_file = "history.txt"
past_titles = []
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        past_titles = [line.strip() for line in f.readlines()]

live_trends = get_daily_trends()

prompt = f"""
أنت رئيس تحرير موقع عالمي مزدوج اللغة (عربي وإنجليزي) متخصص في المجالات الأكثر متابعة:
1. أدوات الذكاء الاصطناعي المجانية وحيل الهواتف والتقنية.
2. الإنتاجية والربح من المنتجات الرقمية.
3. العلوم المبسطة والغرائب المعرفية.

الكلمات الرائجة اليوم: {live_trends}
المقالات السابقة (تجنب تكرارها): {past_titles[-20:]}

اختر موضوعاً واحداً قوياً جداً وعالي البحث، واكتب عنه مقالين مفصلين واحترافيين بصيغة Markdown (نسخة عربية متكاملة ونسخة إنجليزية متكاملة) مع عناوين فرعية ## وقوائم نقطية.

أجب بصيغة JSON صالح فقط (بدون أي نصوص إضافية قبله أو بعده) بهذا الهيكل الدقيق:
{{
  "image_prompt": "Modern digital art illustration representing the tech/science topic, vibrant colors, 4k, no text",
  "ar": {{
    "title": "عنوان المقال الجذاب بالعربية",
    "description": "وصف قصير لمحركات البحث بالعربية",
    "category": "تقنية",
    "content": "محتوى المقال العربي كاملاً بصيغة Markdown"
  }},
  "en": {{
    "title": "Catchy SEO English Article Title",
    "description": "Short SEO meta description in English",
    "category": "AI-Tech",
    "content": "Full English article content in Markdown"
  }}
}}
"""

model = genai.GenerativeModel('gemini-3.8-flash')

response = None
for attempt in range(3):
    try:
        response = model.generate_content(prompt)
        break
    except Exception as e:
        print(f"محاولة رقم {attempt + 1} فشلت، الانتظار 15 ثانية... الخطأ: {e}")
        time.sleep(15)

if not response:
    raise Exception("فشلت محاولات الاتصال.")

raw_text = response.text

if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

data = json.loads(raw_text)

os.makedirs("_posts", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")

# استخدام تصنيفات افتراضية آمنة في حال عدم وجودها
ar_title = data.get('ar', {}).get('title', 'مقال تقني جديد')
ar_cat = data.get('ar', {}).get('category', 'تقنية')
ar_content = data.get('ar', {}).get('content', 'محتوى المقال قيد التحديث.')

en_title = data.get('en', {}).get('title', 'New Tech Article')
en_cat = data.get('en', {}).get('category', 'AI-Tech')
en_content = data.get('en', {}).get('content', 'Article content coming soon.')

# حفظ المقال العربي
ar_filename = f"_posts/{date_str}-{ar_title.replace(' ', '-').lower()[:30]}.md"
ar_frontmatter = f"""---
layout: post
title: "{ar_title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000')}
categories: [{ar_cat}]
lang: ar
---

{ar_content}
"""
with open(ar_filename, "w", encoding="utf-8") as f:
    f.write(ar_frontmatter)

# حفظ المقال الإنجليزي
en_filename = f"_posts/{date_str}-en-{en_title.replace(' ', '-').lower()[:30]}.md"
en_frontmatter = f"""---
layout: post
title: "{en_title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000')}
categories: [{en_cat}]
lang: en
---

{en_content}
"""
with open(en_filename, "w", encoding="utf-8") as f:
    f.write(en_frontmatter)

with open(history_file, "a", encoding="utf-8") as f:
    f.write(en_title + "\n")

print("تم توليد ونشر المقالات بنجاح تام وبشكل آمن!")

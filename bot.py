import os
import json
import datetime
import urllib.parse
import xml.etree.ElementTree as ET
import requests

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"

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
    "category": "تقنية-ومعرفة",
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

headers = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

payload = {
    "model": "claude-3-5-haiku-20241022",
    "max_tokens": 4000,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
res_json = response.json()
raw_text = res_json["content"][0]["text"]
article = json.loads(raw_text)

img_prompt = urllib.parse.quote(article["image_prompt"])
image_url = f"https://image.pollinations.ai/prompt/{img_prompt}?width=1024&height=576&nologo=true"

now = datetime.datetime.now()
date_str = now.strftime("%Y-%m-%d")
time_slug = now.strftime("%H%M%S")

# حفظ النسخة العربية
ar_data = article["ar"]
ar_file = f"_posts/{date_str}-ar-{time_slug}.md"
ar_md = f"""---
layout: post
title: "{ar_data['title'].replace('"', '')}"
description: "{ar_data['description'].replace('"', '')}"
date: {now.strftime("%Y-%m-%d %H:%M:%S")} +0000
categories: {ar_data['category']}
---

![{ar_data['title']}]({image_url})

{ar_data['content']}
"""
with open(ar_file, "w", encoding="utf-8") as f:
    f.write(ar_md)

# حفظ النسخة الإنجليزية
en_data = article["en"]
en_file = f"_posts/{date_str}-en-{time_slug}.md"
en_md = f"""---
layout: post
title: "{en_data['title'].replace('"', '')}"
description: "{en_data['description'].replace('"', '')}"
date: {now.strftime("%Y-%m-%d %H:%M:%S")} +0000
categories: {en_data['category']}
---

![{en_data['title']}]({image_url})

{en_data['content']}
"""
with open(en_file, "w", encoding="utf-8") as f:
    f.write(en_md)

with open(history_file, "a", encoding="utf-8") as f:
    f.write(ar_data["title"] + " | " + en_data["title"] + "\n")

print("تم نشر المقالين عبر Claude Haiku بنجاح!")

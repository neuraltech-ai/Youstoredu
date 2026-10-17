import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

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
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "anthropic/claude-3-haiku",
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
res_json = response.json()

try:
    raw_text = res_json["choices"][0]["message"]["content"]
except Exception as e:
    print(f"API Error Response: {res_json}")
    raise e

# تنظيف وتحليل الـ JSON الناتج من الذكاء الاصطناعي
if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

data = json.loads(raw_text)

os.makedirs("_posts", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")

# حفظ المقال العربي
ar_filename = f"_posts/{date_str}-{data['ar']['title'].replace(' ', '-').lower()[:30]}.md"
ar_frontmatter = f"""---
layout: post
title: "{data['ar']['title']}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000')}
categories: [{data['ar']['category']}]
lang: ar
---

{data['ar']['content']}
"""
with open(ar_filename, "w", encoding="utf-8") as f:
    f.write(ar_frontmatter)

# حفظ المقال الإنجليزي
en_filename = f"_posts/{date_str}-en-{data['en']['title'].replace(' ', '-').lower()[:30]}.md"
en_frontmatter = f"""---
layout: post
title: "{data['en']['title']}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000')}
categories: [{data['en']['category']}]
lang: en
---

{data['en']['content']}
"""
with open(en_filename, "w", encoding="utf-8") as f:
    f.write(en_frontmatter)

# حفظ العنوان في السجل لتجنب تكراره مستقبلاً
with open(history_file, "a", encoding="utf-8") as f:
    f.write(data['en']['title'] + "\n")

print("تم توليد ونشر المقالات بنجاح!")

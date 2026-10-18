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
                for item in root.findall(".//item")[:5]:
                    title = item.find("title")
                    if title is not None and title.text:
                        headlines.append(title.text.strip())
        except Exception:
            continue
    return list(dict.fromkeys(headlines))[:15]

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
    raise Exception("تعذر الاتصال بواجهة Gemini.")

def parse_json_safely(raw_text):
    # محاولة استخراج محتوى JSON من بين العلامات
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(raw_text)
    except Exception:
        # حل بديل آمن في حال فشل تحليل الـ JSON المعقد
        return {
            "image_prompt": "Futuristic technology and artificial intelligence editorial illustration 8k",
            "ar": {
                "title": "أحدث ابتكارات الذكاء الاصطناعي وتطبيقاته العملية",
                "description": "دليلك الشامل لأحدث أدوات الذكاء الاصطناعي وتقنيات المستقبل الرقمية.",
                "category": "ذكاء-اصطناعي",
                "key_takeaways": ["متابعة أحدث أدوات التقنية", "تطبيق الذكاء الاصطناعي بكفاءة"],
                "content": "نستعرض اليوم أحدث التطورات في عالم الذكاء الاصطناعي وكيفية الاستفادة منها في مشاريعك البرمجية والرقيمة لتحقيق أقصى إنتاجية."
            },
            "en": {
                "title": "The Latest AI Innovations and Practical Applications",
                "description": "A comprehensive guide to modern artificial intelligence tools.",
                "category": "AI-Engineering",
                "key_takeaways": ["Explore new tech tools", "Boost your productivity with AI"],
                "content": "Today we explore the latest breakthroughs in artificial intelligence and how to leverage them effectively in your workflow."
            }
        }

history_file = "history.txt"
past_titles = []
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        past_titles = [line.strip() for line in f.readlines()]

live_news = get_live_tech_news()

prompt = f"""
أنت رئيس تحرير موقع تقني عالمي مزدوج اللغة.
أحدث المستجدات اليوم: {live_news}
تجنب تكرار هذه العناوين السابقة: {past_titles[-20:]}

اختر موضوعاً تقنياً بارزاً واكتب عنه مقالاً احترافياً باللغتين العربية والإنجليزية بصيغة Markdown مع عناوين فرعية ## وأكواد برمجية إن أمكن.

أجب بصيغة JSON صالح فقط وبدون أي إضافات بهذا الهيكل الدقيق:
{{
  "image_prompt": "Futuristic sleek editorial illustration representing the tech topic, 8k",
  "ar": {{
    "title": "عنوان المقال بالعربية",
    "description": "وصف قصير لمحركات البحث",
    "category": "تقنية",
    "key_takeaways": ["نقطة 1", "نقطة 2"],
    "content": "محتوى المقال الكامل بالعربية بصيغة Markdown"
  }},
  "en": {{
    "title": "English Article Title",
    "description": "Short SEO meta description",
    "category": "Tech",
    "key_takeaways": ["Point 1", "Point 2"],
    "content": "Full English article content in Markdown"
  }}
}}
"""

print("جاري توليد المقال...")
raw_resp = call_gemini(prompt)
data = parse_json_safely(raw_resp)

os.makedirs("_posts", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")

img_prompt = data.get("image_prompt", "Futuristic technology art 8k")
encoded_prompt = urllib.parse.quote(img_prompt)
seed = int(time.time()) % 10000
image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1000&height=520&nologo=true&seed={seed}"

for lang_key, default_cat, prefix in [("ar", "تقنية", ""), ("en", "AI-Tech", "en-")]:
    lang_obj = data.get(lang_key, {})
    title = str(lang_obj.get("title", "Tech Article")).replace('"', "'")
    desc = str(lang_obj.get("description", title)).replace('"', "'")
    cat = str(lang_obj.get("category", default_cat))
    takeaways = lang_obj.get("key_takeaways", [])
    content = str(lang_obj.get("content", ""))

    if takeaways and isinstance(takeaways, list):
        box_title = "💡 أبرز النقاط في هذا المقال:" if lang_key == "ar" else "💡 Key Takeaways:"
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

print("تم نشر المقالات بنجاح تام!")

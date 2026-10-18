import os
import re
import json
import time
import urllib.parse
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import google.generativeai as genai

api_keys = [
    os.environ.get("ANTHROPIC_API_KEY"),
    os.environ.get("GEMINI2"),
    os.environ.get("GEMINI3")
]
api_keys = [k for k in api_keys if k]

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

def call_gemini_with_rotation(prompt_text):
    for i, key in enumerate(api_keys):
        for model_name in ['gemini-3.8-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt_text)
                if response and response.text:
                    return response.text
            except Exception as e:
                time.sleep(1)
    return None

history_file = "history.txt"
past_titles = []
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        past_titles = [line.strip() for line in f.readlines()]

live_news = get_live_tech_news()
news_title = live_news[0] if live_news else "Advanced AI Engineering & Automation"

prompt = f"""
أنت رئيس تحرير موقع تقني عالمي مزدوج اللغة.
أحدث المستجدات اليوم: {live_news}
اكتب مقالاً تقنياً احترافياً وعميقاً باللغتين العربية والإنجليزية بصيغة JSON صالح فقط بهذا الهيكل الدقيق وبدون أي نص خارجه:
{{
  "ar": {{
    "title": "أحدث تطورات الذكاء الاصطناعي والأتمتة الرقمية الحديثة",
    "description": "دليلك الشامل لأحدث أدوات وتقنيات الذكاء الاصطناعي الرقمية وكيفية توظيفها برمجياً.",
    "category": "تقنية",
    "key_takeaways": ["فهم أحدث تقنيات الأتمتة", "تطبيق الذكاء الاصطناعي بكفاءة"],
    "content": "نستعرض اليوم أحدث التطورات في عالم الذكاء الاصطناعي والبرمجة الحديثة وكيفية الاستفادة منها في تطوير مشاريعك الرقمية لتحقيق أقصى إنتاجية.\n\n```python\n# مثال عملي للأتمتة بالذكاء الاصطناعي\nimport os\nprint('NeuralTech AI Autonomous Engine Running...')\n```"
  }},
  "en": {{
    "title": "Latest Breakthroughs in Artificial Intelligence and Automation",
    "description": "A comprehensive guide to modern AI tools and software engineering automation.",
    "category": "AI-Engineering",
    "key_takeaways": ["Explore modern automation workflows", "Boost software engineering productivity"],
    "content": "Today we explore the latest breakthroughs in artificial intelligence and how software engineers can leverage them effectively in their daily workflows.\n\n```python\n# Practical AI Automation Snippet\nimport os\nprint('NeuralTech AI Autonomous Engine Running...')\n```"
  }}
}}
"""

raw_resp = call_gemini_with_rotation(prompt)

if raw_resp and "```json" in raw_resp:
    raw_resp = raw_resp.split("```json")[1].split("```")[0].strip()
elif raw_resp and "```" in raw_resp:
    raw_resp = raw_resp.split("```")[1].split("```")[0].strip()

try:
    data = json.loads(raw_resp)
except Exception:
    data = {
        "ar": {
            "title": f"ثورة الذكاء الاصطناعي: {news_title[:40]}",
            "description": "تحليل لأحدث المستجدات التقنية وأدوات البرمجة الحديثة.",
            "category": "تقنية",
            "key_takeaways": ["متابعة أحدث التقنيات العالمية", "تطوير المهارات البرمجية الذكية"],
            "content": f"نناقش اليوم أبرز المستجدات التقنية العالمية المتعلقة بـ: {news_title}\n\n```python\n# NeuralTech AI Execution Engine\nprint('System Online & Fully Operational')\n```"
        },
        "en": {
            "title": f"AI Revolution: {news_title[:40]}",
            "description": "An in-depth analysis of modern tech trends and engineering tools.",
            "category": "AI-Engineering",
            "key_takeaways": ["Track cutting-edge tech trends", "Leverage intelligent automation"],
            "content": f"Today we examine the latest global technological breakthroughs regarding: {news_title}\n\n```python\n# NeuralTech AI Execution Engine\nprint('System Online & Fully Operational')\n```"
        }
    }

os.makedirs("_posts", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")

# قائمة صور تقنية ثابتة وعالية الجودة تعمل للأبد دون أي حدود
tech_images = [
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=1200&auto=format&fit=crop"
]
image_url = tech_images[int(time.time()) % len(tech_images)]

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

print("تم التحديث بنجاح واعتماد الصور التقنية المستقرة!")

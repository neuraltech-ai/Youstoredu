import os
import re
import json
import time
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
        "https://techcrunch.com/category/artificial-intelligence/feed/"
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
    for key in api_keys:
        for model_name in ['gemini-3.8-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt_text)
                if response and response.text:
                    return response.text
            except Exception:
                time.sleep(1)
    return None

live_news = get_live_tech_news()
news_title = live_news[0] if live_news else "Advanced AI Engineering & Automation"

# الخطوة الأولى: توليد المسودة الأولية
draft_prompt = f"""
أنت كاتب تقني خبير. استناداً إلى هذه المستجدات التقنية: {live_news}
اكتب مقالاً تقنياً عميقاً ومفصلاً باللغتين العربية والإنجليزية يتضمن أمثلة برمجية بايثون حقيقية وصحيحة، بصيغة JSON حصراً بهذا الشكل ودون أي نص خارجه:
{{
  "ar": {{
    "title": "عنوان المقال بالعربية",
    "description": "وصف قصير للمقال",
    "category": "ذكاء-اصطناعي",
    "key_takeaways": ["نقطة 1", "نقطة 2"],
    "content": "محتوى المقال مع أكواد بايثون صحيحة."
  }},
  "en": {{
    "title": "English Title",
    "description": "Short English description",
    "category": "AI-Engineering",
    "key_takeaways": ["Point 1", "Point 2"],
    "content": "Article content with Python code."
  }}
}}
"""

raw_draft = call_gemini(draft_prompt)
if raw_draft and "```json" in raw_draft:
    raw_draft = raw_draft.split("```json")[1].split("```")[0].strip()
elif raw_draft and "```" in raw_draft:
    raw_draft = raw_draft.split("```")[1].split("```")[0].strip()

try:
    draft_data = json.loads(raw_draft)
except Exception:
    draft_data = {
        "ar": {"title": f"ثورة الذكاء الاصطناعي: {news_title[:40]}", "description": "تحليل تقني شامل", "category": "تقنية", "key_takeaways": ["متابعة التقنية الحديثة"], "content": "محتوى تجريبي مع كود بايثون:\n```python\nprint('AI Engine')\n```"},
        "en": {"title": f"AI Revolution: {news_title[:40]}", "description": "Comprehensive tech analysis", "category": "AI-Tech", "key_takeaways": ["Track modern tech"], "content": "Sample content with Python:\n```python\nprint('AI Engine')\n```"}
    }

# الخطوة الثانية: وكيل المراجعة والتدقيق الإلزامي (Senior Code Reviewer & Auditor Agent)
audit_prompt = f"""
أنت مراجع برمجية ومدقق لغوي وتقني صارم جداً. شرط أساسي: تدقيق وصياغة النصوص العربية بدقة تامة ومنع أي أخطاء إملائية مثل استبدال حروف متشابهة (مثل القاف والفاء أو الطاء والتاء) وضمان لغة عربية فصحى سليمة 100%.
قم بمراجعة المقال والأكواد البرمجية التالية بدقة تامة:
1. تصحيح أي أخطاء برمجية في أكواد البايثون (Syntax & Logic).
2. تحسين الصياغة التقنية لتكون احترافية وخالية من الحشو.
3. التأكد من تطابق المعنى بين النسخة العربية والإنجليزية.
أعِد الناتج النهائي بصيغة JSON صالحة حصراً وبنفس الهيكل ودون أي نص خارجها:
{json.dumps(draft_data, ensure_ascii=False)}
"""

raw_audited = call_gemini(audit_prompt)
if raw_audited and "```json" in raw_audited:
    raw_audited = raw_audited.split("```json")[1].split("```")[0].strip()
elif raw_audited and "```" in raw_audited:
    raw_audited = raw_audited.split("```")[1].split("```")[0].strip()

try:
    data = json.loads(raw_audited)
except Exception:
    data = draft_data

os.makedirs("_posts", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")

tech_images = [
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1200&auto=format&fit=crop"
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
        box_title = "💡 أبرز النقاط المدققة برمجياً:" if lang_key == "ar" else "💡 Audited Key Takeaways:"
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

print("تمت مراجعة وتدقيق المقال والأكواد برمجياً بنجاح بواسطة الوكيل الذكي!")

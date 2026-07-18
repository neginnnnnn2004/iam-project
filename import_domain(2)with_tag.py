import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"

import pandas as pd
import requests
from urllib.parse import urlparse
import sys
import unicodedata

API_BASE_URL = "http://127.0.0.1:8000"
BEARER_TOKEN = "در اینجا توکن ادمین احراز هویت شده را قرار دهید"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

def normalize_text(text):
    if not text or pd.isna(text):
        return ""
    text = unicodedata.normalize('NFKC', str(text))
    text = text.strip().lower()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ").replace("\u200b", " ").replace("\xa0", " ")
    return " ".join(text.split())


def clean_domain(url):
    if not url or pd.isna(url):
        return ""
    url = str(url).strip().lower()
    if not url.startswith(('http://', 'https://')):
        url_for_parse = 'http://' + url
    else:
        url_for_parse = url
    try:
        parsed = urlparse(url_for_parse)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        if ':' in domain:
            domain = domain.split(':')[0]
        return domain.strip()
    except Exception:
        return ""


def extract_list_from_response(res_json, url_context=""):
    print(
        f"\n🔍 [عیب‌یابی] کلیدهای پاسخ سرور برای {url_context}: {list(res_json.keys()) if isinstance(res_json, dict) else 'Type is List'}")

    if isinstance(res_json, list):
        return res_json
    if isinstance(res_json, dict):
        for key in ['results', 'data', 'items', 'list']:
            if key in res_json and isinstance(res_json[key], list):
                return res_json[key]
        for val in res_json.values():
            if isinstance(val, list):
                return val
    return []


def fetch_all_pages(start_url):
    all_items = []
    current_url = start_url

    while current_url:
        try:
            res = requests.get(current_url, headers=HEADERS)
            if res.status_code != 200:
                print(f" خطا در دریافت صفحه. کد وضعیت: {res.status_code} برای آدرس {current_url}")
                break

            res_json = res.json()
            page_items = extract_list_from_response(res_json, current_url)
            all_items.extend(page_items)

            if isinstance(res_json, dict) and res_json.get('next'):
                current_url = res_json['next']
                if current_url.startswith('/'):
                    current_url = f"{API_BASE_URL}{current_url}"
            else:
                current_url = None
        except Exception as e:
            print(f" خطای ارتباطی در دریافت صفحه: {e}")
            break

    return all_items


current_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.path.join(current_dir, "لیست سایت های فارسی.xlsx"),
    os.path.join(current_dir, "iam2", "لیست سایت های فارسی.xlsx"),
    os.path.join(current_dir, "..", "لیست سایت های فارسی.xlsx"),
]

file_path = None
for path in possible_paths:
    if os.path.exists(path):
        file_path = path
        break

if not file_path:
    print(" خطا: فایل اکسل یافت نشد!")
    sys.exit(1)

print(f" در حال خواندن و پردازش فایل از مسیر: {file_path}")
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip()

domain_col = df.columns[1]
tag_col = df.columns[2]

df['cleaned_domain'] = df[domain_col].apply(clean_domain)
df = df.dropna(subset=['cleaned_domain', tag_col])
df = df[df['cleaned_domain'] != '']
df_unique = df.drop_duplicates(subset=['cleaned_domain'])

print(" در حال استعلام اطلاعات فعلی سیستم از سرور...")

domains_detail_url = f"{API_BASE_URL}/identity/listOfDomains/"
tags_detail_url = f"{API_BASE_URL}/identity/listOfTags/"

tags_list = fetch_all_pages(tags_detail_url)
existing_domains_list = fetch_all_pages(domains_detail_url)

print(f"\n تعداد کل تگ‌های دریافت شده از سرور: {len(tags_list)}")
print(f" تعداد کل دامنه‌های دریافت شده از سرور: {len(existing_domains_list)}")

server_tags = {}
for t in tags_list:
    if isinstance(t, dict):
        title = t.get('tag') or t.get('tag_title') or t.get('name') or t.get('title')
        if title:
            server_tags[normalize_text(title)] = title

server_domains = {}
for d in existing_domains_list:
    if isinstance(d, dict):
        raw_name = d.get('domain') or d.get('domain_name') or d.get('name') or d.get('url')
        if raw_name:
            cleaned_server_domain = clean_domain(raw_name)
            if cleaned_server_domain:
                server_domains[cleaned_server_domain] = raw_name

assign_tags_payload = []
missing_tags_in_db = set()
missing_domains_in_db = 0

for _, row in df_unique.iterrows():
    d_name = row['cleaned_domain']
    t_title = str(row[tag_col])

    exact_domain_name = server_domains.get(d_name)
    exact_tag_title = server_tags.get(normalize_text(t_title))

    if exact_domain_name and exact_tag_title:
        assign_tags_payload.append({
            "domain_name": exact_domain_name,
            "tag_title": exact_tag_title
        })
    else:
        if not exact_tag_title:
            missing_tags_in_db.add(t_title)
        if not exact_domain_name:
            missing_domains_in_db += 1

print(f"\n وضعیت نهایی نگاشت روابط: تعداد {len(assign_tags_payload)} رابطه آماده ارسال است.")
if missing_tags_in_db:
    print(f" هشدار: این تگ‌ها در سیستم پیدا نشدند: {missing_tags_in_db}")
if missing_domains_in_db > 0:
    print(f" هشدار: تعداد {missing_domains_in_db} دامنه از اکسل در سیستم یافت نشدند.")

if assign_tags_payload:
    assign_url = f"{API_BASE_URL}/identity/assign-a-tag/"
    print(f" در حال انتساب روابط تگ‌ها به دامنه‌ها روی سرور...")
    try:
        response = requests.post(assign_url, headers=HEADERS, json=assign_tags_payload)
        if response.status_code in [200, 201]:
            print(" تبریک! عملیات نهایی کاملاً موفقیت‌آمیز بود و روابط تمام تگ‌ها متصل گردید.")
        elif response.status_code == 409:
            print(" هشدار: روابط این برچسب‌ها از قبل در دیتابیس وجود داشتند.")
        else:
            print(f" خطا در انتساب تگ‌ها! کد وضعیت: {response.status_code}\nمتن خطا: {response.text}")
    except Exception as e:
        print(f" خطای ارتباط در مرحله انتساب نهایی تگ: {e}")
else:
    print(" دیتای معتبری برای متصل کردن تگ یافت نشد. لطفاً خروجی بخش [عیب‌یابی] بالا را بررسی کنید.")
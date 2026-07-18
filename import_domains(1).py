import pandas as pd
import requests
from urllib.parse import urlparse
import json
import os
import sys

API_URL = "http://127.0.0.1:8000/identity/domains/import/"
BEARER_TOKEN = "در اینجا توکن ادمین احراز هویت شده را قرار دهید"
TARGET_GROUP_ID = 1

# clean_domain
def clean_domain(url):
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
        return domain
    except Exception:
        return None


current_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.path.join(current_dir, "Fa_domain (1).xlsx"),
    os.path.join(current_dir, "iam2", "Fa_domain (1).xlsx"),
    os.path.join(current_dir, "..", "Fa_domain (1).xlsx"),
    os.path.join(current_dir, "identity", "Fa_domain (1).xlsx"),
]

file_path = None
for path in possible_paths:
    if os.path.exists(path):
        file_path = path
        break

if not file_path:
    print("خطا: فایل اکسل 'Fa_domain (1).xlsx' در هیچ‌کدام از پوشه‌های پروژه یافت نشد!")
    sys.exit(1)

# read Excel file with panadas
print(f"در حال خواندن و پردازش فایل از مسیر: {file_path}")
df = pd.read_excel(file_path)

domain_column_name = df.columns[1]
df['cleaned_domain'] = df[domain_column_name].apply(clean_domain)

df = df.dropna(subset=['cleaned_domain'])
df = df[df['cleaned_domain'] != '']
df_unique = df.drop_duplicates(subset=['cleaned_domain'])

print(f" آمار پردازش دامنه‌ها:")
print(f"  - تعداد کل رکوردها در فایل: {len(df)}")
print(f"  - تعداد دامنه‌های یکتا و تمیز شده: {len(df_unique)}")

dist_column_name = df.columns[4] if len(df.columns) > 4 else None

domains_to_send = []
for _, row in df_unique.iterrows():
    category_val = row[dist_column_name] if dist_column_name else "نامشخص"

    domains_to_send.append({
        "domain_name": row['cleaned_domain'],
        "description": f"دسته بندی: {category_val}",
        "group_id": [TARGET_GROUP_ID]
    })

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

print(f" در حال ارسال {len(domains_to_send)} دامنه به دیتابیس...")
try:
    response = requests.post(API_URL, headers=headers, json=domains_to_send)

    if response.status_code in [200, 201]:
        print(" عملیات موفقیت‌آمیز بود! تمام دامنه‌ها بدون ارور وارد دیتابیس شدند.")
    else:
        print(f" خطا در ثبت دامنه‌ها! کد وضعیت: {response.status_code}")
        print("پاسخ سرور:", json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f" خطای ارتباط با سرور: {e}")
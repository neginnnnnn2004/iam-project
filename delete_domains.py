import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iam2.settings")
django.setup()

from identity.models import Domain, User_Domain_Tag


print("Deleting all domains...")

# ابتدا ارتباط‌های مربوط به Domain را حذف می‌کنیم
User_Domain_Tag.objects.all().delete()

# سپس خود Domainها را حذف می‌کنیم
deleted_count, _ = Domain.objects.all().delete()

print(f"Deleted {deleted_count} records.")
print("All domains deleted successfully.")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from identity.models import Domain, User_Domain_Tag


print("Deleting all domains...")

# First, remove the connections related to the domain.
User_Domain_Tag.objects.all().delete()

# Then, delete the domains.
deleted_count, _ = Domain.objects.all().delete()

print(f"Deleted {deleted_count} records.")
print("All domains deleted successfully.")
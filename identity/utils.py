import secrets
import string
from django.contrib.auth.hashers import make_password, check_password
from identity.models import Backup_Code


def generate_random_backup_code(length=8):
    friendly_characters = "3456789ABCDEFGHJKLMNPQRSTUVWXY"
    code = "".join(secrets.choice(friendly_characters) for _ in range(length))
    return code


def create_user_backup_codes(user, count=8):
    raw_codes = []
    for _ in range(count):
        raw_code = generate_random_backup_code()
        raw_codes.append(raw_code)

        hashed_code = make_password(raw_code)

        Backup_Code.objects.create(
            user=user,
            hash_code=hashed_code,
            is_used=False
        )
    return raw_codes


def verify_and_use_backup_code(user, backup_code):
    unused_codes = Backup_Code.objects.filter(user=user, is_used=False)
    for code_obj in unused_codes:
        if check_password(backup_code, code_obj.hash_code):
            code_obj.is_used = True
            code_obj.save()
            return True
    return False
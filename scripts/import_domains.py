import os
import django
import pandas as pd
from urllib.parse import urlparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from identity.models import User, Domain, Tag, User_Domain_Tag, Group

def extract_root_domain(url_or_domain: str) -> str:
    url_or_domain = str(url_or_domain).strip().lower()
    if not url_or_domain.startswith(("http://", "https://")):
        url_or_domain = "http://" + url_or_domain

    parsed = urlparse(url_or_domain)
    domain_name = parsed.hostname

    if not domain_name:
        return ""

    if domain_name.startswith("www."):
        domain_name = domain_name[4:]

    return domain_name
#####define path files#####
file_path1 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data/لیست سایت های فارسی.xlsx"
)

file_path2 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data/Fa_domain (1).xlsx"
)

def import_with_tags(file_path1, username):
    print(f"Starting import from: {file_path1}")
    df = pd.read_excel(file_path1)
    print(f"Excel rows: {len(df)}")

    user = User.objects.get(username=username)
    general_group = Group.objects.get(id=1)

    print(f"Using user: {user.username}")
    print(f"Using group: {general_group.title}")

    for _, row in df.iterrows():

        domain_name = row["ادرس"]
        tag_name = row["دسته بندی"]

        #skip null rows
        if pd.isna(domain_name) or pd.isna(tag_name):
            continue

        #create domain obj
        domain_name = extract_root_domain(domain_name)
        tag_name = str(tag_name).strip()

        domain_obj, created = Domain.objects.get_or_create(
            domain_name=domain_name,
            defaults={
                "groups": general_group
            }
        )

        if created:
            print(f"Created domain: {domain_name}")
        else:
            print(f"Domain already exists: {domain_name}")


        #find tag obj
        try:
            tag_obj = Tag.objects.get(title=tag_name)
        except Tag.DoesNotExist:
            print(f"Tag not found: {tag_name}")
            continue

        # bond User + Domain + Tag
        User_Domain_Tag.objects.get_or_create(
            user=user,
            domain=domain_obj,
            tag=tag_obj
        )

        print(
            f"Imported: {domain_name} -> {tag_name} -> general"
        )

    print("Import finished successfully!")


#####################################################
def import_domain_without_tags(file_path2, username):
    print(f"Starting import from: {file_path2}")

    df = pd.read_excel(file_path2)

    print(f"Excel rows: {len(df)}")

    user = User.objects.get(username=username)
    general_group = Group.objects.get(id=1)

    print(f"Using user: {user.username}")
    print(f"Using group: {general_group.title}")

    for _, row in df.iterrows():

        domain_name = row["domain"]

        # skip null rows
        if pd.isna(domain_name):
            continue

        # extract domain
        domain_name = extract_root_domain(domain_name)

        if not domain_name:
            continue

        # create domain
        domain_obj, created = Domain.objects.get_or_create(
            domain_name=domain_name,
            defaults={
                "groups": general_group
            }
        )

        if created:
            print(f"Created domain: {domain_name}")
        else:
            print(f"Domain already exists: {domain_name}")

    print("Import without tags finished successfully!")


if __name__ == "__main__":

    # Excel 1
    # Domain + Tag + User + General
    import_with_tags(
        file_path1,
        "admin"
    )

    # Excel 2
    # Domain + General
    import_domain_without_tags(
        file_path2,
        "admin"
    )
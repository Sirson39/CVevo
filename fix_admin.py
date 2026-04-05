import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvevo.settings')
django.setup()

from core.models import User

# Update by email (case-insensitive)
users = User.objects.filter(email__iexact='admin@cvevo.com')
print(f"Found {users.count()} entries matching admin@cvevo.com")

for u in users:
    print(f"Updating {u.email} (current name: {u.full_name})")
    u.full_name = 'CVevo Admin'
    u.role = 'admin'
    u.is_verified = True
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print("Update successful!")

# Double check
all_admins = User.objects.filter(is_staff=True)
print("\nAll Staff Users in DB:")
for a in all_admins:
    print(f"- {a.email} | {a.full_name} | {a.role}")

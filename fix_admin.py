import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cvevo.settings')
django.setup()

from core.models import User

ADMIN_EMAIL = "admin@cvevo.com"
ADMIN_PASSWORD = "sirson"
ADMIN_NAME = "CVevo Admin"


def ensure_admin_user():
    user = User.objects.filter(email__iexact=ADMIN_EMAIL).first()
    created = False

    if not user:
        user = User(email=ADMIN_EMAIL, full_name=ADMIN_NAME, role="admin")
        created = True

    user.full_name = ADMIN_NAME
    user.role = "admin"
    user.is_verified = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(ADMIN_PASSWORD)
    user.save()
    return user, created


if __name__ == "__main__":
    user, created = ensure_admin_user()
    state = "Created" if created else "Updated"
    print(f"{state} admin user: {user.email}")
    print("Admin login:")
    print(f"  email: {ADMIN_EMAIL}")
    print(f"  password: {ADMIN_PASSWORD}")

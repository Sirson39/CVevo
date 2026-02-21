from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import JobseekerProfile, HRProfile

@receiver(user_signed_up)
def create_profile_on_google_signup(request, user, **kwargs):
    acct = request.session.pop("oauth_account_type", "jobseeker")
    full_name = (user.get_full_name() or user.email.split("@")[0]).strip()

    if acct == "hr":
        HRProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": full_name, "company": "—", "role": "—"},
        )
    else:
        JobseekerProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": full_name},
        )

from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import JobseekerProfile, HRProfile

@receiver(user_logged_in)
def ensure_profile_on_login(sender, request, user, **kwargs):
    # If HR profile exists, OK
    if HRProfile.objects.filter(user=user).exists():
        return

    # If Jobseeker profile exists, OK
    if JobseekerProfile.objects.filter(user=user).exists():
        return

    # If none exists, create jobseeker by default
    full_name = (user.get_full_name() or user.email.split("@")[0]).strip()
    JobseekerProfile.objects.get_or_create(user=user, defaults={"full_name": full_name})


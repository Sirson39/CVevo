from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from allauth.account.signals import user_signed_up
from .models import JobseekerProfile, HRProfile, User

@receiver(user_signed_up)
def create_profile_on_google_signup(request, user, **kwargs):
    sociallogin = kwargs.get("sociallogin")
    acct = request.session.pop("oauth_account_type", None)
    
    # Extra safety: HR should not be created via Google
    if acct == "hr":
        return

    # Default to jobseeker if coming from google_start
    user.role = "jobseeker"
    
    # Try to get full name from Google extra data
    full_name = ""
    if sociallogin:
        extra_data = sociallogin.account.extra_data
        full_name = extra_data.get("name", "")
    
    if not full_name:
        full_name = user.full_name or user.email.split("@")[0]
    
    user.full_name = full_name
    user.save()

    JobseekerProfile.objects.get_or_create(
        user=user,
        defaults={"full_name": full_name, "email": user.email},
    )


from allauth.socialaccount.signals import pre_social_login
from django.shortcuts import redirect
from django.contrib import messages
from allauth.core.exceptions import ImmediateHttpResponse

@receiver(pre_social_login)
def block_hr_social_login(request, sociallogin, **kwargs):
    # If the user already exists and is an HR, block social login
    email = sociallogin.user.email
    if email:
        try:
            existing_user = User.objects.get(email=email)
            if existing_user.role == "hr":
                messages.error(request, "This account is registered as HR. Google login is not allowed for HR accounts.")
                raise ImmediateHttpResponse(redirect("login"))
        except User.DoesNotExist:
            pass

@receiver(user_logged_in)
def ensure_profile_on_login(sender, request, user, **kwargs):
    # If any profile exists, we are good
    if hasattr(user, 'hr_profile') or hasattr(user, 'jobseeker_profile'):
        return

    # If no profile, check session for intent
    acct = request.session.pop("oauth_account_type", None)
    if not acct or acct == "hr":
        return

    # Role already set or need setting?
    if user.role != "jobseeker":
        user.role = "jobseeker"
        user.save()

    full_name = user.full_name or user.email.split("@")[0]
    JobseekerProfile.objects.get_or_create(
        user=user,
        defaults={"full_name": full_name, "email": user.email},
    )


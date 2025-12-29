from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, UploadedResume
from .models import JobDescription

# --- User Signup ---
class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# --- User Login ---
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

# --- Resume Upload ---
class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedResume
        fields = ['file']


class JobDescriptionForm(forms.ModelForm):
    class Meta:
        model = JobDescription
        fields = ['title', 'file']

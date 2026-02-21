# core/forms.py
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Education, Experience, Project, Skill


class BaseRegisterForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        cpw = cleaned.get("confirm_password")

        if pw and cpw and pw != cpw:
            self.add_error("confirm_password", "Passwords do not match.")

        if pw:
            validate_password(pw)

        return cleaned


class JobseekerRegisterForm(BaseRegisterForm):
    pass


class HRRegisterForm(BaseRegisterForm):
    company = forms.CharField(max_length=120)
    role = forms.CharField(max_length=120)


class ResumeUploadForm(forms.Form):
    resume_file = forms.FileField(
        label="Select Resume (PDF or DOCX)",
        help_text="Max size: 5MB"
    )

    def clean_resume_file(self):
        file = self.cleaned_data.get("resume_file")
        if file:
            # Check extension
            ext = file.name.split(".")[-1].lower()
            if ext not in ["pdf", "docx"]:
                raise ValidationError("Only PDF and DOCX files are allowed.")
            
            # Check size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be under 5MB.")
                
        return file


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ["institution", "degree", "start_date", "end_date", "description"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["company", "position", "start_date", "end_date", "description"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "link", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "level"]

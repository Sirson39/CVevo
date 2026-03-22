# core/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Education, Experience, Project, Skill

User = get_user_model()


class BaseRegisterForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, required=False) # validate in clean
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    def __init__(self, *args, **kwargs):
        self.user_is_authenticated = kwargs.pop("user_is_authenticated", False)
        super().__init__(*args, **kwargs)
        if self.user_is_authenticated:
            self.fields["email"].required = False
            self.fields["password"].required = False
            self.fields["confirm_password"].required = False
        else:
            self.fields["email"].required = True
            self.fields["password"].required = True
            self.fields["confirm_password"].required = True

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not self.user_is_authenticated:
            if not email:
                raise ValidationError("Email is required.")
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        cpw = cleaned.get("confirm_password")

        if not self.user_is_authenticated:
            if not pw:
                self.add_error("password", "Password is required.")
            elif pw and cpw and pw != cpw:
                self.add_error("confirm_password", "Passwords do not match.")
            
            if pw:
                validate_password(pw)

        return cleaned


class JobseekerRegisterForm(BaseRegisterForm):
    pass


class HRRegisterForm(BaseRegisterForm):
    company = forms.CharField(max_length=120, label="Company Name")
    role = forms.CharField(max_length=120, label="Job Title / Position")


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    remember = forms.BooleanField(required=False)


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


class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["full_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.email

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class SupportTicketForm(forms.Form):
    TOPICS = [
        ("Account / Login", "Account / Login"),
        ("Resume Upload", "Resume Upload"),
        ("ATS Analysis", "ATS Analysis"),
        ("Resume Builder", "Resume Builder"),
        ("Export / Downloads", "Export / Downloads"),
        ("Other", "Other"),
    ]
    PRIORITIES = [
        ("Normal", "Normal"),
        ("High", "High"),
        ("Urgent", "Urgent"),
    ]
    topic = forms.ChoiceField(choices=TOPICS)
    priority = forms.ChoiceField(choices=PRIORITIES)
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)

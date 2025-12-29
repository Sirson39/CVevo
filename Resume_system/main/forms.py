from django import forms
from .models import ResumeUpload

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = ResumeUpload
        fields = ['resume_file']
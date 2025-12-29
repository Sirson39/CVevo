from django.db import models

class UserResume(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    skills = models.TextField()
    education = models.TextField()
    experience = models.TextField()
    summary = models.TextField()
    pdf_file = models.FileField(upload_to="resumes/", null=True, blank=True)

    def __str__(self):
        return self.name


class HRJob(models.Model):
    job_title = models.CharField(max_length=200)
    job_description = models.TextField()

    def __str__(self):
        return self.job_title


class HRUploadedResume(models.Model):
    job = models.ForeignKey(HRJob, on_delete=models.CASCADE)
    resume_file = models.FileField(upload_to="resumes/")
    extracted_text = models.TextField(null=True, blank=True)
    match_score = models.FloatField(default=0)

    def __str__(self):
        return self.resume_file.name
    

from django.db import models

class ResumeUpload(models.Model):
    resume_file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# -------------------------------------------
# USER PROFILE WITH ROLES
# -------------------------------------------
class UserProfile(models.Model):
    USER_TYPES = (
        ('normal', 'Normal User'),
        ('org', 'Organization'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='normal')

    # OPTIONAL FIELDS
    organization_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


# Create user profile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# Save profile automatically when updating User model
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


# -------------------------------------------
# RESUME UPLOAD STORAGE (for AI checker)
# -------------------------------------------
class UploadedResume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    extracted_text = models.TextField(blank=True, null=True)  # For ATS NLP
    score = models.IntegerField(null=True, blank=True)        # ATS Score
    issues = models.TextField(blank=True, null=True)          # JSON list as text

    def __str__(self):
        return f"Resume by {self.user.username} ({self.uploaded_at.date()})"


# -------------------------------------------
# ORGANIZATION SCREENING RESULT STORAGE
# -------------------------------------------
class ScreeningResult(models.Model):
    organization = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.ForeignKey(UploadedResume, on_delete=models.CASCADE)
    matched_score = models.IntegerField()
    matched_skills = models.TextField()
    missing_skills = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ScreeningResult {self.matched_score} - {self.organization.username}"



class JobDescription(models.Model):
    organization = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='job_descriptions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} by {self.organization.username}"

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from .utils import OverwriteStorage


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    role = models.CharField(
        max_length=20, 
        choices=[('jobseeker', 'Jobseeker'), ('hr', 'HR')], 
        default='jobseeker'
    )
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class JobseekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="jobseeker_profile")
    full_name = models.CharField(max_length=120)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=120, blank=True)
    linkedin = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    selected_template = models.CharField(max_length=50, default='modern_professional')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Jobseeker: {self.full_name} ({self.user.email})"


class Education(models.Model):
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="educations")
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class Experience(models.Model):
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="experiences")
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.position} at {self.company}"


class Project(models.Model):
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=200)
    link = models.URLField(blank=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Skill(models.Model):
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=50, choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')], default='Intermediate')

    def __str__(self):
        return self.name


class HRProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hr_profile")
    full_name = models.CharField(max_length=120)
    company = models.CharField(max_length=120)
    role = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HR: {self.full_name} - {self.company} ({self.user.email})"


class JobPost(models.Model):
    hr = models.ForeignKey(HRProfile, on_delete=models.CASCADE, related_name="job_posts")
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(help_text="Expected keywords for ATS matching")
    status = models.CharField(max_length=20, choices=[('Open', 'Open'), ('Closed', 'Closed')], default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Resume(models.Model):
    jobseeker = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="resumes", null=True, blank=True)
    file = models.FileField(upload_to="resumes/%Y/%m/%d/", storage=OverwriteStorage())
    filename = models.CharField(max_length=255)
    source = models.CharField(max_length=50, choices=[('Jobseeker', 'Jobseeker'), ('HR Bulk', 'HR Bulk')], default='Jobseeker')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.jobseeker.full_name} - {self.filename}"


class ParsedResumeData(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="parsed_data")
    extracted_text = models.TextField()
    name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    skills = models.TextField(blank=True)  # JSON-like or comma separated
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)

    def __str__(self):
        return f"Parsed data for {self.resume.filename}"


class ATSResult(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="ats_results")
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="ats_results", null=True, blank=True)
    custom_job_title = models.CharField(max_length=255, blank=True, help_text="Used for quick scans without a formal job post")
    score = models.FloatField()
    feedback = models.TextField()
    matched_keywords = models.TextField(blank=True)
    missing_keywords = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def matched_list(self):
        if not self.matched_keywords: return []
        return [k.strip() for k in self.matched_keywords.split(',') if k.strip()]
    
    @property
    def missing_list(self):
        if not self.missing_keywords: return []
        return [k.strip() for k in self.missing_keywords.split(',') if k.strip()]

    @property
    def concise_feedback(self):
        # If it's already concise (from the new analyzer), return as is
        if not self.feedback.strip().startswith("1. **Final ATS Score**"):
            return self.feedback
        
        # fallback for old "messy" reports: build a summary from other fields
        matched_count = len(self.matched_list)
        missing_count = len(self.missing_list)
        total = matched_count + missing_count
        
        msg = f"Matched {matched_count} out of {total} requirements identified in this analysis. "
        if self.missing_list:
            msg += f"Recommended additions: {', '.join(self.missing_list[:3])}."
        return msg

    def __str__(self):
        return f"{self.resume.jobseeker.full_name} match for {self.job_post.title}: {self.score}%"

class Notification(models.Model):
    TYPE_CHOICES = [('success','Success'),('info','Info'),('warning','Warning'),('error','Error')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=300)
    icon = models.CharField(max_length=10, default='??')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.user.email}: {self.message[:60]}'

    @classmethod
    def push(cls, user, message, icon='??', notif_type='info'):
        cls.objects.create(user=user, message=message, icon=icon, type=notif_type)
        keep_ids = list(cls.objects.filter(user=user).values_list('id', flat=True)[:4])
        cls.objects.filter(user=user).exclude(id__in=keep_ids).delete()

class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

class SupportRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_messages")
    topic = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=[("Normal", "Normal"), ("High", "High"), ("Urgent", "Urgent")], default="Normal")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.subject} ({self.priority})"

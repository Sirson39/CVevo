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
        choices=[('jobseeker', 'Jobseeker'), ('hr', 'HR'), ('admin', 'Admin')], 
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
    SKILL_TYPES = [('Technical', 'Technical Skill'), ('Soft', 'Soft Skill')]
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)
    skill_type = models.CharField(max_length=20, choices=SKILL_TYPES, default='Technical')
    level = models.CharField(max_length=50, choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')], default='Intermediate')

    def __str__(self):
        return f"{self.name} ({self.skill_type})"


class Certificate(models.Model):
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="certificates")
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    date_obtained = models.DateField(null=True, blank=True)
    link = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Reference(models.Model):
    profile = models.ForeignKey(JobseekerProfile, on_delete=models.CASCADE, related_name="references")
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=100, help_text="e.g. Former Manager")
    company = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Reference: {self.name} ({self.company})"


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
    required_skills = models.TextField(blank=True, help_text="Comma separated skills")
    experience_requirements = models.TextField(blank=True)
    education_requirements = models.TextField(blank=True)
    tools_and_technologies = models.TextField(blank=True, help_text="Specific tools or software")
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
        owner = self.jobseeker.full_name if self.jobseeker else "Bulk Upload"
        return f"{owner} - {self.filename}"


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
    status = models.CharField(max_length=50, choices=[
        ('Applied', 'Applied'),
        ('Shortlisted', 'Shortlisted'),
        ('Interviewing', 'Interviewing'),
        ('Rejected', 'Rejected')
    ], default='Applied')
    
    @property
    def matched_list(self):
        if not self.matched_keywords: return []
        return [k.strip() for k in self.matched_keywords.split(',') if k.strip()]
    
    @property
    def missing_list(self):
        if not self.missing_keywords: return []
        return [k.strip() for k in self.missing_keywords.split(',') if k.strip()]

    @property
    def general_scan_data(self):
        """Parses the feedback field as JSON if it's a general quality scan."""
        import json
        if self.feedback.startswith('{') and self.feedback.endswith('}'):
            try:
                return json.loads(self.feedback)
            except:
                return None
        return None

    @property
    def concise_feedback(self):
        # If it's a general scan, return the summary
        data = self.general_scan_data
        if data:
            return data.get('summary', '')
            
        # If it's already concise (from the new analyzer), return as is
        if not self.feedback.strip().startswith("1. **Final ATS Score**"):
            return self.feedback

    def __str__(self):
        job_title = self.job_post.title if self.job_post else self.custom_job_title or "Quick Scan"
        candidate_name = self.resume.jobseeker.full_name if self.resume.jobseeker else "Candidate"
        return f"{candidate_name} match for {job_title}: {self.score}%"

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
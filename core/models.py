from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
    file = models.FileField(upload_to="resumes/%Y/%m/%d/")
    filename = models.CharField(max_length=255)
    source = models.CharField(max_length=50, choices=[('Jobseeker', 'Jobseeker'), ('HR Bulk', 'HR Bulk')], default='Jobseeker')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.jobseeker.full_name} - {self.filename}"


class ParsedResumeData(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="parsed_data")
    extracted_text = models.TextField()
    skills = models.TextField(blank=True)  # JSON-like or comma separated
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)

    def __str__(self):
        return f"Parsed data for {self.resume.filename}"


class ATSResult(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="ats_results")
    job_post = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="ats_results")
    score = models.FloatField()
    feedback = models.TextField()
    matched_keywords = models.TextField(blank=True)
    missing_keywords = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resume.jobseeker.full_name} match for {self.job_post.title}: {self.score}%"

# Generated manually to align migration state with the current core models.

import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone

import core.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(max_length=120)),
                ("role", models.CharField(choices=[("jobseeker", "Jobseeker"), ("hr", "HR")], default="jobseeker", max_length=20)),
                ("is_verified", models.BooleanField(default=False)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", core.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="HRProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                ("company", models.CharField(max_length=120)),
                ("role", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="hr_profile", to="core.user")),
            ],
        ),
        migrations.CreateModel(
            name="JobPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("requirements", models.TextField(help_text="Expected keywords for ATS matching")),
                ("status", models.CharField(choices=[("Open", "Open"), ("Closed", "Closed")], default="Open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("hr", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_posts", to="core.hrprofile")),
            ],
        ),
        migrations.CreateModel(
            name="JobseekerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("location", models.CharField(blank=True, max_length=120)),
                ("linkedin", models.URLField(blank=True)),
                ("portfolio", models.URLField(blank=True)),
                ("summary", models.TextField(blank=True)),
                ("selected_template", models.CharField(default="modern_professional", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="jobseeker_profile", to="core.user")),
            ],
        ),
        migrations.CreateModel(
            name="Education",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("institution", models.CharField(max_length=200)),
                ("degree", models.CharField(max_length=200)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("description", models.TextField(blank=True)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="educations", to="core.jobseekerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="Experience",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company", models.CharField(max_length=200)),
                ("position", models.CharField(max_length=200)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("description", models.TextField()),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="experiences", to="core.jobseekerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("link", models.URLField(blank=True)),
                ("description", models.TextField()),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="core.jobseekerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="Resume",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(storage=core.models.OverwriteStorage(), upload_to="resumes/%Y/%m/%d/")),
                ("filename", models.CharField(max_length=255)),
                ("source", models.CharField(choices=[("Jobseeker", "Jobseeker"), ("HR Bulk", "HR Bulk")], default="Jobseeker", max_length=50)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("jobseeker", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="resumes", to="core.jobseekerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="ParsedResumeData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("extracted_text", models.TextField()),
                ("name", models.CharField(blank=True, max_length=255)),
                ("role", models.CharField(blank=True, max_length=255)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("skills", models.TextField(blank=True)),
                ("experience", models.TextField(blank=True)),
                ("education", models.TextField(blank=True)),
                ("resume", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="parsed_data", to="core.resume")),
            ],
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("level", models.CharField(choices=[("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")], default="Intermediate", max_length=50)),
                ("profile", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skills", to="core.jobseekerprofile")),
            ],
        ),
        migrations.CreateModel(
            name="ATSResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.FloatField()),
                ("feedback", models.TextField()),
                ("matched_keywords", models.TextField(blank=True)),
                ("missing_keywords", models.TextField(blank=True)),
                ("analyzed_at", models.DateTimeField(auto_now_add=True)),
                ("job_post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ats_results", to="core.jobpost")),
                ("resume", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ats_results", to="core.resume")),
            ],
        ),
    ]

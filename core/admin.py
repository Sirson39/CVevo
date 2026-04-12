from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, JobseekerProfile, HRProfile, Resume, JobPost, ATSResult, ContactMessage, SupportRequest, Education, Experience, Project, Skill, Certificate, Reference, ParsedResumeData

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "full_name", "role", "is_verified", "is_staff")
    search_fields = ("email", "full_name")
    ordering = ("email",)
    
    # Required for custom user models with email as USERNAME_FIELD
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "role", "is_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password"),
        }),
    )

admin.site.register(JobseekerProfile)
admin.site.register(HRProfile)
admin.site.register(ParsedResumeData)

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("jobseeker", "file", "uploaded_at")
    list_filter = ("uploaded_at",)

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("title", "hr", "status", "created_at")
    list_filter = ("status", "created_at")
admin.site.register(ATSResult)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Project)
admin.site.register(Skill)
admin.site.register(Certificate)
admin.site.register(Reference)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "is_resolved")
    list_filter = ("is_resolved", "created_at")
    search_fields = ("name", "email", "subject", "message")
    ordering = ("-created_at",)

@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "priority", "subject", "created_at", "is_resolved")
    list_filter = ("is_resolved", "priority", "topic", "created_at")
    search_fields = ("user__email", "subject", "message")
    ordering = ("-created_at",)


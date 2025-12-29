from django.contrib import admin
from .models import UserProfile, UploadedResume, JobDescription, ScreeningResult

admin.site.register(UserProfile)
admin.site.register(UploadedResume)
admin.site.register(JobDescription)
admin.site.register(ScreeningResult)

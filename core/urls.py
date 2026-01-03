from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", lambda r: views.page(r, "auth-login.html"), name="login"),
    path("register/", lambda r: views.page(r, "auth-register.html"), name="register"),

    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("resume-tips/", views.resume_tips, name="resume_tips"),
    path("ats-guide/", views.ats_guide, name="ats_guide"),

    path("jobseeker/dashboard/", lambda r: views.page(r, "jobseeker-dashboard.html")),
    path("analysis/results/", lambda r: views.page(r, "analysis-results.html")),
    path("resume/builder/", lambda r: views.page(r, "resume-builder.html")),
    path("templates/", lambda r: views.page(r, "templates.html")),
    path("export/", lambda r: views.page(r, "export.html")),
    path("profile/", lambda r: views.page(r, "profile.html")),

    path("hr/dashboard/", lambda r: views.page(r, "hr-dashboard.html")),
    path("hr/jd/create/", lambda r: views.page(r, "jd-create.html")),
    path("hr/job-posts/", lambda r: views.page(r, "job-posts.html")),
    path("hr/resume-upload/", lambda r: views.page(r, "resume-upload.html")),
    path("hr/ranking/", lambda r: views.page(r, "ranking.html")),
    path("hr/candidate/", lambda r: views.page(r, "candidate-detail.html")),
    path("hr/reports/", lambda r: views.page(r, "reports.html")),
    path("organizations/", views.organizations, name="organizations"),
]

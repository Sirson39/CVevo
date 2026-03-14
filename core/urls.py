# core/urls.py
from django.urls import path
from core import views

urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register_choose, name="register_choose"),
    path("register/jobseeker/", views.register_jobseeker, name="register_jobseeker"),
    path("register/hr/", views.register_hr, name="register_hr"),
    path("login/", views.login_page, name="login"),

    path("auth/google/<str:acct>/", views.google_start, name="google_start"),
    path("post-login/", views.post_login_redirect, name="post_login_redirect"),

    # landing resources pages
    path("resume-tips/", views.resume_tips, name="resume_tips"),
    path("ats-guide/", views.ats_guide, name="ats_guide"),
    path("organizations/", views.organizations, name="organizations"),

    path("app/home/", lambda r: views.page(r, "app_home.html"), name="app_home"),


    #  Jobseeker pages (now protected in views.py)
    path("jobseeker/dashboard/", views.jobseeker_dashboard, name="jobseeker_dashboard"),
    path("resume-upload/",        views.resume_upload,        name="resume_upload"),
    path("resume-delete/<int:pk>/", views.resume_delete,       name="resume_delete"),
    path("analysis/results/",     views.analysis_results,            name="analysis_results"),
    path("analysis/analyze/<int:resume_id>/", views.analyze_resume, name="analyze_resume"),
    path("resume/builder/",       views.resume_builder,              name="resume_builder"),
    path("resume/builder/education/add/", views.add_education, name="add_education"),
    path("resume/builder/education/delete/<int:pk>/", views.delete_education, name="delete_education"),
    path("resume/builder/experience/add/", views.add_experience, name="add_experience"),
    path("resume/builder/experience/delete/<int:pk>/", views.delete_experience, name="delete_experience"),
    path("resume/builder/project/add/", views.add_project, name="add_project"),
    path("resume/builder/project/delete/<int:pk>/", views.delete_project, name="delete_project"),
    path("resume/builder/skill/add/", views.add_skill, name="add_skill"),
    path("resume/builder/skill/delete/<int:pk>/", views.delete_skill, name="delete_skill"),
    path("templates/",            lambda r: views.page(r, "templates_gallery.html"),    name="templates_gallery"),
    path("export/",               lambda r: views.page(r, "export_downloads.html"),     name="export_downloads"),
    path("profile/",              lambda r: views.page(r, "profile_settings.html"),     name="profile_settings"),
    path("jobseeker/help-support/", views.help_support, name="help_support"),


    #  HR pages (now protected in views.py)
    path("hr/dashboard/",         views.hr_dashboard,         name="hr_dashboard"),
    path("hr/jd/create/",         views.hr_create_job,        name="hr_create_job"),
    path("hr/job-posts/",         views.hr_manage_jobs,       name="hr_manage_jobs"),
    path("hr/resume-upload/",     lambda r: views.page(r, "hr_resume_upload.html"),     name="hr_resume_upload"),
    path("hr/ranking/",           lambda r: views.page(r, "hr_candidate_ranking.html"), name="hr_candidate_ranking"),
    path("hr/candidate/",         lambda r: views.page(r, "hr_candidate_detail.html"),  name="hr_candidate_detail"),
    path("hr/reports/",           lambda r: views.page(r, "hr_reports_export.html"),    name="hr_reports_export"),
]
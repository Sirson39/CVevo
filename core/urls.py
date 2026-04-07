# core/urls.py
from django.urls import path
from core import views

urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register_choose, name="register_choose"),
    path("register/jobseeker/", views.register_jobseeker, name="register_jobseeker"),
    path("register/hr/", views.register_hr, name="register_hr"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("auth/google/<str:acct>/", views.google_start, name="google_start"),
    path("post-login/", views.post_login_redirect, name="post_login_redirect"),

    # landing resources pages
    path("resume-tips/", views.resume_tips, name="resume_tips"),
    path("ats-guide/", views.ats_guide, name="ats_guide"),
    path("organizations/", views.organizations, name="organizations"),
    path("contact/", views.contact_view, name="contact_us"),

    path("app/home/", lambda r: views.page(r, "app_home.html"), name="app_home"),


    #  Jobseeker pages (now protected in views.py)
    path("jobseeker/dashboard/", views.jobseeker_dashboard, name="jobseeker_dashboard"),
    path("resume-upload/",        views.resume_upload,        name="resume_upload"),
    path("resume-parse-result/<int:resume_id>/", views.resume_parse_result, name="resume_parse_result"),
    path("resume-delete/<int:pk>/", views.resume_delete,       name="resume_delete"),
    path("analysis/results/",     views.analysis_results,            name="analysis_results"),
    path("analysis/delete/<int:pk>/", views.delete_analysis_result, name="delete_analysis_result"),
    path("analysis/analyze/<int:resume_id>/", views.analyze_resume, name="analyze_resume"),
    path("analysis/general/<int:resume_id>/", views.general_analysis, name="general_analysis"),
    path("analysis/quick-analysis/", views.quick_analysis, name="quick_analysis"),
    path("resume/builder/",       views.resume_builder,              name="resume_builder"),
    path("resume/builder/education/add/", views.add_education, name="add_education"),
    path("resume/builder/education/delete/<int:pk>/", views.delete_education, name="delete_education"),
    path("resume/builder/experience/add/", views.add_experience, name="add_experience"),
    path("resume/builder/experience/delete/<int:pk>/", views.delete_experience, name="delete_experience"),
    path("resume/builder/project/add/", views.add_project, name="add_project"),
    path("resume/builder/project/delete/<int:pk>/", views.delete_project, name="delete_project"),
    path("resume/builder/skill/add/", views.add_skill, name="add_skill"),
    path("resume/builder/skill/delete/<int:pk>/", views.delete_skill, name="delete_skill"),
    path("resume/builder/certificate/add/", views.add_certificate, name="add_certificate"),
    path("resume/builder/certificate/delete/<int:pk>/", views.delete_certificate, name="delete_certificate"),
    path("resume/builder/reference/add/", views.add_reference, name="add_reference"),
    path("resume/builder/reference/delete/<int:pk>/", views.delete_reference, name="delete_reference"),
    path("templates/",            lambda r: views.page(r, "templates_gallery.html"),    name="templates_gallery"),
    path("templates/select/<str:template_name>/", views.select_template, name="select_template"),
    path("export/",               views.export_downloads,               name="export_downloads"),
    path("export/docx/",          views.export_resume_docx,             name="export_resume_docx"),
    path("profile/",              views.profile_settings,                               name="profile_settings"),
    path("jobseeker/help-support/", views.help_support, name="help_support"),
    path("search/", views.dashboard_search, name="dashboard_search"),


    #  HR pages (now protected in views.py)
    path("hr/dashboard/",         views.hr_dashboard,         name="hr_dashboard"),
    path("hr/jd/create/",         views.hr_create_job,        name="hr_create_job"),
    path("hr/job-posts/",         views.hr_manage_jobs,       name="hr_manage_jobs"),
    path("hr/job/delete/<int:job_id>/", views.hr_delete_job,   name="hr_delete_job"),
    path("hr/resume-upload/",     views.hr_resume_upload,     name="hr_resume_upload"),
    path("hr/ranking/",           views.hr_candidate_ranking, name="hr_candidate_ranking"),
    path("hr/candidate/",         views.hr_candidate_detail,  name="hr_candidate_detail"),
    path("hr/candidate/update-status/", views.hr_update_candidate_status, name="hr_update_status"),
    path("hr/reports/",           views.hr_reports_export,    name="hr_reports_export"),
    path("hr/reports/export-csv/", views.hr_export_csv,       name="hr_export_csv"),

    # Notifications
    path("notifications/read/",   views.mark_notifications_read, name="mark_notifications_read"),
    path("export/pdf/notify/",    views.notify_pdf_export, name="notify_pdf_export"),
    # Internal Admin Suite
    path("internal/dashboard/", views.internal_admin_dashboard, name="super_admin_dashboard"),
    path("internal/users/", views.admin_users_view, name="admin_users"),
    path("internal/jobs/", views.admin_jobs_view, name="admin_jobs"),
    path("internal/resumes/", views.admin_resumes_view, name="admin_resumes"),
    path("internal/ats/", views.admin_ats_view, name="admin_ats"),
    path("internal/support/", views.admin_support_view, name="admin_support"),
    
    # Internal Admin Actions
    path("internal/user/delete/<int:pk>/", views.admin_delete_user, name="admin_delete_user"),
    path("internal/job/delete/<int:pk>/", views.admin_delete_job, name="admin_delete_job"),
    path("internal/resume/delete/<int:pk>/", views.admin_delete_resume, name="admin_delete_resume"),
    path("internal/support/resolve/<int:pk>/", views.admin_resolve_support, name="admin_resolve_support"),
    path("internal/support/delete/<int:pk>/", views.admin_delete_support, name="admin_delete_support"),

    
    # Internal Admin Edit/Create
    path("internal/user/create/", views.admin_create_user, name="admin_create_user"),
    path("internal/user/edit/<int:pk>/", views.admin_edit_user, name="admin_edit_user"),
    path("internal/job/edit/<int:pk>/", views.admin_edit_job, name="admin_edit_job"),
    path("internal/resume/view/<int:pk>/", views.admin_view_resume, name="admin_view_resume"),
]

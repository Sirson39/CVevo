from django.urls import path
from django.shortcuts import redirect
from core import views

urlpatterns = [
    path("", views.home, name="home"),
    path("post-login/", views.post_login_redirect, name="post_login_redirect"),
    
    # Redirect legacy template URLs to the new decoupled frontend pages
    path("login/", lambda r: redirect('/pages/public/login.html'), name="login"),
    path("register/", lambda r: redirect('/pages/public/auth-register-choose.html'), name="register_choose"),
    path("jobseeker/dashboard/", lambda r: redirect('/pages/jobseeker/jobseeker_dashboard.html'), name="jobseeker_dashboard"),
    path("hr/dashboard/", lambda r: redirect('/pages/hr/hr_dashboard.html'), name="hr_dashboard"),
    
    # Social Auth & Utilities
    path("auth/google/<str:acct>/", views.google_start, name="google_start"),
    path("notifications/read/", views.mark_notifications_read, name="mark_notifications_read"),
]

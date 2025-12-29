from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.org_dashboard, name='org_dashboard'),
    path('upload-jd/', views.upload_job_description, name='upload_jd'),
    path('match-history/', views.match_history, name='match_history'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('export-csv/', views.export_csv, name='export_csv'),




]

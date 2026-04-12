from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'jobseeker-profiles', api_views.JobseekerProfileViewSet)
router.register(r'hr-profiles', api_views.HRProfileViewSet)
router.register(r'job-posts', api_views.JobPostViewSet)
router.register(r'resumes', api_views.ResumeViewSet)
router.register(r'ats-results', api_views.ATSResultViewSet)
router.register(r'notifications', api_views.NotificationViewSet)
router.register(r'support-requests', api_views.SupportRequestViewSet)
router.register(r'contact-messages', api_views.ContactMessageViewSet)

urlpatterns = [
    # Auth endpoints
    path('auth/', api_views.AuthView.as_view(), name='api_auth'),
    path('auth/login/', api_views.AuthView.as_view(), {'action': 'login'}, name='api_login'),
    path('auth/register-jobseeker/', api_views.AuthView.as_view(), {'action': 'register-jobseeker'}, name='api_register_jobseeker'),
    path('auth/register-hr/', api_views.AuthView.as_view(), {'action': 'register-hr'}, name='api_register_hr'),
    path('auth/logout/', api_views.AuthView.as_view(), {'action': 'logout'}, name='api_logout'),
    path('users/me/', api_views.UserMeView.as_view(), name='api_user_me'),
    
    # Dashboard endpoints
    path('jobseeker/dashboard/', api_views.JobseekerDashboardView.as_view(), name='api_jobseeker_dashboard'),
    # HR specific endpoints
    path('hr/dashboard/', api_views.HRDashboardView.as_view(), name='api_hr_dashboard'),
    path('hr/manage-jobs/', api_views.JobPostViewSet.as_view({'get': 'list'}), name='api_hr_manage_jobs'),
    path('hr/jobs/', api_views.JobPostViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_hr_jobs_list'),
    path('hr/jobs/<int:pk>/', api_views.JobPostViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='api_hr_jobs_detail'),
    path('hr/candidate-ranking/', api_views.HRCandidateRankingView.as_view(), name='api_hr_candidate_ranking'),
    path('hr/candidate-detail/', api_views.HRCandidateDetailView.as_view(), name='api_hr_candidate_detail'),
    path('hr/update-status/', api_views.HRUpdateStatusView.as_view(), name='api_hr_update_status'),
    path('hr/resume-upload/jobs/', api_views.JobPostViewSet.as_view({'get': 'list'}), name='api_hr_resume_upload_jobs'),
    path('hr/resume-upload/', api_views.HRBulkUploadView.as_view(), name='api_hr_bulk_upload'),
    path('hr/bulk-upload/', api_views.HRBulkUploadView.as_view(), name='api_hr_bulk_upload_alias'),
    
    # Analysis endpoints
    path('analysis/quick/', api_views.QuickAnalysisView.as_view(), name='api_quick_analysis'),
    path('analysis/general/<int:resume_id>/', api_views.GeneralAnalysisView.as_view(), name='api_general_analysis'),
    
    # Resume Builder endpoints
    path('resume-builder/templates/', api_views.TemplateGalleryView.as_view(), name='api_templates_list'),
    path('resume-builder/templates/select/', api_views.TemplateGalleryView.as_view(), {'action': 'select'}, name='api_templates_select'),
    path('resume-builder/', api_views.ResumeBuilderView.as_view(), name='api_resume_builder'),
    path('resume-builder/profile/', api_views.ResumeBuilderView.as_view(), name='api_resume_builder_profile'),
    path('resume-builder/<str:category>/', api_views.ResumeBuilderActionView.as_view(), name='api_resume_builder_add'),
    path('resume-builder/<str:category>/<int:pk>/', api_views.ResumeBuilderActionView.as_view(), name='api_resume_builder_delete'),
    
    path('', include(router.urls)),
]

from django.urls import path
from screening import views as screen_views
from main import views as main_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # your urls here...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path('', main_views.home, name='home'),
    path('logout/', screen_views.user_logout, name='logout'),
    path('upload/', views.resume_upload, name='resume_upload'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

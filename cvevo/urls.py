from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve
import os

urlpatterns = [
    path("sysadmin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    
    # The New Heart: The API
    path("api/", include("core.api_urls")),
    
    # Main Site redirection
    path("", include("core.urls")),

    # Serve the decoupled frontend and uploaded media in both development and production.
    path('assets/<path:path>', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'frontend', 'assets'),
    }),
    path('pages/<path:path>', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'frontend', 'pages'),
    }),
    path('partials/<path:path>', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'frontend', 'partials'),
    }),
    path('media/<path:path>', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

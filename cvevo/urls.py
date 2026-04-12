from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

urlpatterns = [
    path("sysadmin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    
    # The New Heart: The API
    path("api/", include("core.api_urls")),
    
    # Main Site redirection
    path("", include("core.urls")),
]

if settings.DEBUG:
    # Serving Media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # DIRECT ACCESS to the new decoupled frontend assets
    # This ensures "assets/cvevo/..." works immediately
    urlpatterns += [
        path('assets/<path:path>', serve, {
            'document_root': os.path.join(settings.BASE_DIR, 'frontend', 'assets'),
        }),
        # Allow serving pages directly if needed
        path('pages/<path:path>', serve, {
            'document_root': os.path.join(settings.BASE_DIR, 'frontend', 'pages'),
        }),
        path('partials/<path:path>', serve, {
            'document_root': os.path.join(settings.BASE_DIR, 'frontend', 'partials'),
        }),
    ]

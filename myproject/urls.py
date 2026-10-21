from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from myproject.views import database_keepalive, terminal_status_view


def health_check(request):
    return JsonResponse({"status": "ok", "message": "Backend is active"})


urlpatterns = [
    path("", terminal_status_view, name="terminal-status"),
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="api-health-check"),
    path("api/health/db/", database_keepalive, name="database-keepalive"),
    path("health", health_check, name="health-check"),
    path("health/", health_check, name="health-check-slash"),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

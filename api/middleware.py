import time
from django.utils.deprecation import MiddlewareMixin
from .models import RequestLog
from django.contrib.auth import get_user_model

User = get_user_model()

class APIPerformanceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if request.path == '/api/upload-file/' and hasattr(request, 'user') and request.user.is_authenticated:
            response_time = time.time() - request.start_time
            RequestLog.objects.create(
                user=request.user,
                endpoint=request.path,
                status_code=response.status_code,
                response_time=response_time,
                success=response.status_code < 400
            )
        return response
from django_ratelimit.core import is_ratelimited
from django.http import JsonResponse

class ApiRateLimitMiddleware:
    """
    Middleware to apply rate limiting to all requests under /api/.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Apply rate limiting only to /api/ paths
        if request.path.startswith('/api/'):
            # Check if the request exceeds the rate limit
            limited = is_ratelimited(
                request=request,
                group="api",  # Define a unique group for API rate limiting
                key='ip',
                rate='2/m',  # 2 requests per minute
                method=['GET', 'POST'],  # Add methods you want to limit
                increment=True,
            )
            if limited:
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

        return self.get_response(request)
"""
Simple views for the config app.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint.
    
    Returns:
        JSON response with API status
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'TechMart API',
        'version': '1.0.0',
        'message': 'API is running successfully'
    })

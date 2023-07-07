from django.http import JsonResponse
from rest_framework.decorators import api_view


@api_view(['GET'])
def description(request):
    """
    api/admin/
    API description response with URLs to list resources
    """
    description = {
        'description': 'Open ONI Admin API for automating management tasks',
        'title': 'Open ONI Admin API',
    }
    return JsonResponse(description, safe=False)

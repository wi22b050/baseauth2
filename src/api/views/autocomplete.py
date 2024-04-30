from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
from rest_framework.permissions import IsAuthenticated

UserModel = get_user_model()
# If further types are to be included, they should be added here: 
allowed_types = {
    'users': UserModel,
    'titles': UserModel,
    'keywords': UserModel,
    'locations': UserModel,
}

source_name = getattr(settings, 'AUTOCOMPLETE_SOURCE', 'baseauth')
permission_classes = (IsAuthenticated,)

@extend_schema(
    tags=['autocomplete'],
    parameters=[
        OpenApiParameter(name='query', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Search for part of the user's name", required=True),
        OpenApiParameter(name='type', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Type of autocomplete", required=False),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Maximum number of results to return", required=False),
    ],
    operation_id='autocomplete_user_name',
    summary="Autocomplete user names",
    description="Returns a list of user names matching the provided query."
)
@api_view(['GET'])
def autocomplete_user(request, *args, **kwargs):
    query = request.GET.get('query', '')
    try:
        limit = int(request.GET.get('limit', 10)) 
    except ValueError:
        return Response({"detail": "Limit must be an integer."}, status=400)

    type_requested = request.GET.get('type', 'users').split(',')
    valid_types = [t.strip() for t in type_requested if t.strip() in allowed_types]

    if not valid_types:
        return Response({"detail": f"Invalid type parameter, allowed types are: {list(allowed_types.keys())}"}, status=400)

    response_data = []

    for type_requested in valid_types:
        search_results = allowed_types[type_requested].objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).distinct()[:limit]

        individual_response_data = {
            "id": type_requested,
            "label": f"Autocomplete results for {type_requested}",
            "data": [
                {
                    "id": user.username,
                    "source_name": source_name,
                    "label": f"{user.first_name} {user.last_name}"
                } for user in search_results
            ]
        }
        
        response_data.append(individual_response_data)
    
    if len(response_data[0]['data']) == 1:
        return Response(response_data[0]['data'][0])
    else:
        return Response(response_data)


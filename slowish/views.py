from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def tokens(request):

    response = {"unauthorized":
                {"code": 401,
                 "message":
                 "Unable to authenticate user with credentials provided."}}

    return JsonResponse(response, status=401)

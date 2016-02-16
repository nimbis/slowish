from datetime import datetime, timedelta
import json

from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader

from .models import SlowishUser


def unauthorized():
    unauth_response = {
        "unauthorized":
        {"code": 401,
         "message":
         "Unable to authenticate user with credentials provided."}}

    return JsonResponse(unauth_response, status=401)


@csrf_exempt
def tokens(request):

    try:
        jreq = json.loads(request.body)
        account_id = jreq['auth']['tenantId']
        username = jreq['auth']['passwordCredentials']['username']
        password = jreq['auth']['passwordCredentials']['password']
        user = SlowishUser.objects.get(
            account__id=account_id,
            username=username,
            password=password)
    except:
        return unauthorized()

    expiration = datetime.utcnow() + timedelta(days=2)

    template = loader.get_template('slowish/tokens.json')
    context = {
        "user": user,
        "expires": expiration.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return HttpResponse(
        template.render(context, request),
        content_type="application/json")


@csrf_exempt
def account(request, account_id):
    return HttpResponse("Not yet implemented.")

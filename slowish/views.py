from datetime import datetime, timedelta
import json

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.shortcuts import get_object_or_404

from .models import SlowishAccount, SlowishUser, SlowishContainer


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

    # The base URL we want to use is whatever is being used in the
    # current request, but without any path, (not even a trailing
    # slash). Use reverse on '/' to compute it with a final '/' and
    # then the [:-1] slice to drop that.
    base_url = request.build_absolute_uri('/')[:-1]

    template = loader.get_template('slowish/tokens.json')
    context = {
        "user": user,
        "expires": expiration.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_url": base_url
    }
    return HttpResponse(
        template.render(context, request),
        content_type="application/json")


@csrf_exempt
def account(request, account_id):
    try:
        SlowishUser.objects.get(
            account__id=account_id,
            token=request.META['HTTP_X_AUTH_TOKEN'])
    except:
        return unauthorized()

    containers = SlowishContainer.objects.filter(account__id=account_id)

    # Note: The need for safe=False is documented here:
    #
    # https://docs.djangoproject.com/en/1.9/ref/request-response/#jsonresponse-objects
    # The safety concern is really a non-issue for us:
    #
    #   * As described above, this was only a concern with old browsers
    #
    #   * We don't expect browsers to be using this API anyway
    #
    #   * Regardless, we're implemeting the Swift API which has an
    #     array return-value at this point, so there's nothing we
    #     can change and remain compatible.
    return JsonResponse(
        [{"count": 0,
          "bytes": 0,
          "name": container.name} for container in containers],
        safe=False)


@csrf_exempt
def container(request, account_id, container_name):
    try:
        SlowishUser.objects.get(
            account__id=account_id,
            token=request.META['HTTP_X_AUTH_TOKEN'])
    except:
        return unauthorized()

    account = get_object_or_404(SlowishAccount, id=account_id)

    if (request.method == 'PUT'):
        (container, created) = SlowishContainer.objects.get_or_create(
            account=account,
            name=container_name)
        if (created):
            return HttpResponse('', status=201)  # Created
        else:
            return HttpResponse('', status=200)  # OK

    # For request.method == 'GET' (and anything else really)
    get_object_or_404(SlowishContainer,
                      account=account,
                      name=container_name)
    return HttpResponse('', status=204)  # No content

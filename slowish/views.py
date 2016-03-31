from datetime import datetime, timedelta
import json

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.shortcuts import get_object_or_404

from .models import SlowishAccount, SlowishUser, SlowishContainer, SlowishFile


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
        try:
            account_id = jreq['auth']['tenantId']
        except:
            account_id = jreq['auth']['tenantName']
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
    containers = containers.order_by('name')

    if request.GET:
        try:
            marker = request.GET['marker']
            containers = filter(lambda(x): x.name > marker, containers)
        except KeyError:
            pass

        try:
            end_marker = request.GET['end_marker']
            containers = filter(lambda(x): x.name < end_marker, containers)
        except KeyError:
            pass

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


def container_put(request, account, container_name, path):
    (container, container_created) = SlowishContainer.objects.get_or_create(
        account=account,
        name=container_name)

    if (path != ''):
        (file, file_created) = SlowishFile.objects.get_or_create(
            container=container,
            path=path)
    else:
        file_created = False

    if (container_created or file_created):
        return HttpResponse('', status=201)  # Created
    else:
        return HttpResponse('', status=200)  # OK


# We haven't yet implemented support for storing fie contents, but a
# GET of a file path is still useful for distinguishing whether it
# exists in the container or not.
def container_get_file(request, container, path):
    try:
        SlowishFile.objects.get(container=container, path=path)
        return HttpResponse('', status=200)  # OK
    except:
        return HttpResponse('', status=404)


def container_get_contents(request, container):

    files = SlowishFile.objects.filter(container=container).order_by("path")

    if request.GET:
        if "prefix" in request.GET:
            files = files.filter(path__startswith=request.GET["prefix"])

        if "marker" in request.GET:
            files = files.filter(path__gt=request.GET["marker"])

        if "end_marker" in request.GET:
            files = files.filter(path__lt=request.GET["end_marker"])

    # See comment by call to JsonResponse above for justification of safe=False
    return JsonResponse(
        [{"bytes": 0,
          "name": file.path,
          "content_type": "application/directory"} for file in files],
        safe=False)


@csrf_exempt
def container(request, account_id, container_name, path=''):
    try:
        SlowishUser.objects.get(
            account__id=account_id,
            token=request.META['HTTP_X_AUTH_TOKEN'])
    except:
        return unauthorized()

    account = get_object_or_404(SlowishAccount, id=account_id)

    if (request.method == 'PUT'):
        return container_put(request, account, container_name, path)

    container = get_object_or_404(
        SlowishContainer,
        account=account,
        name=container_name)

    if path == '':
        return container_get_contents(request, container)
    else:
        return container_get_file(request, container, path)

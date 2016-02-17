from django.shortcuts import render


def introduction(request):

    context = {
        "base_url": request.build_absolute_uri('/')
    }

    return render(request, 'slowish/introduction.html', context)

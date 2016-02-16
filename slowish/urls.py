from django.conf.urls import url

from slowish import views

urlpatterns = [
    url(r'^tokens$', views.tokens, name='tokens'),

    url(r'^files/(?P<account_id>[0-9]+)$',
        views.account,
        name='account'),

    url(r'^files/(?P<account_id>[0-9]+)/(?P<container_name>[^/]*)',
        views.container,
        name='container')
]

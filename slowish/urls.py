from django.conf.urls import url

from slowish import views

urlpatterns = [
    url(r'^tokens$', views.tokens, name='tokens'),
]

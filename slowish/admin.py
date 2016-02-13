from django.contrib import admin

from .models import SlowishAccount, SlowishUser

admin.site.register(SlowishAccount)
admin.site.register(SlowishUser)

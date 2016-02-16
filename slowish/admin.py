from django.contrib import admin

from .models import SlowishAccount, SlowishUser, SlowishContainer

admin.site.register(SlowishAccount)
admin.site.register(SlowishUser)
admin.site.register(SlowishContainer)

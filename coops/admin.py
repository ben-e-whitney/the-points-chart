from django.contrib import admin

# Register your models here.

import coops.models

admin.site.register(coops.models.Coop)
admin.site.register(coops.models.Cooper)

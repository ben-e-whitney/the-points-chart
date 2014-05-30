from django.contrib import admin

# Register your models here.

import profiles.models

admin.site.register(profiles.models.UserProfile)
admin.site.register(profiles.models.GroupProfile)

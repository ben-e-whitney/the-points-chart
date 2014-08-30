from django.contrib import admin

import profiles.models

admin.site.register(profiles.models.UserProfile)
admin.site.register(profiles.models.GroupProfile)

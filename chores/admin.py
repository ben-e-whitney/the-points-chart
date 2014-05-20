from django.contrib import admin

# Register your models here.

import chores.models

admin.site.register(chores.models.Chore)
admin.site.register(chores.models.ChoreInstance)

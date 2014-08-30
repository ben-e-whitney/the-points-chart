from django.contrib import admin

import chores.models

admin.site.register(chores.models.Signature)
admin.site.register(chores.models.Timecard)
admin.site.register(chores.models.ChoreSkeleton)
admin.site.register(chores.models.Chore)

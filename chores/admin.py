from django.contrib import admin

# Register your models here.

import chores.models

# class SignatureInline(admin.StackedInline):
    # model = chores.models.Signature
    # extra = 3

# class TimecardAdmin(admin.ModelAdmin):
    # inlines = [SignatureInline]

# admin.site.register(chores.models.Timecard, TimecardAdmin)
# admin.site.register(chores.models.Signature)
# admin.site.register(chores.models.Timecard)
admin.site.register(chores.models.ChoreSkeleton)
admin.site.register(chores.models.Chore)

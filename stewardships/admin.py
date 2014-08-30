from django.contrib import admin

import stewardships.models

admin.site.register(stewardships.models.StewardshipSkeleton)
admin.site.register(stewardships.models.Stewardship)
# Imagining absences and share changes being one-off things, so there seems no
# reason to register this skeleton. Note that this is inconsistent with what
# has been done with the stewardships and chores.
# admin.site.register(stewardships.models.BenefitChangeSkeleton)
admin.site.register(stewardships.models.Absence)
admin.site.register(stewardships.models.ShareChange)

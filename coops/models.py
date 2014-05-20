from django.db import models

# Create your models here.

from django.contrib.auth.models import User, Group
import timezone_field
import localflavor.us.forms

# TODO: look into the 'unique' field option
# <https://docs.djangoproject.com/en/dev/ref/models/fields/#unique>
# Some things should definitely not be unique, though -- for example Chores,
# since we want to allow partway through a semester
class Coop(Group):
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    time_zone = timezone_field.TimeZoneField()
    # Preferences.
    email_prefix = models.CharField(max_length=2**6, default='[Points]',
                                    null=True, blank=True)

    def __str__(self):
        return self.short_name

class Cooper(User):
    # TODO: in admin display, display full_name instead of first_name and
    # last_name, maybe.
    full_name = models.CharField(max_length=2**6)
    display_name = models.CharField(max_length=2**6)
    # TODO: At least for now, this complains if we give it 'blank=True'.
    phone_number = localflavor.us.forms.USPhoneNumberField()
    # TODO: somewhere this needs to be checked against a table of carriers and
    # gateways. Where to do this?
    phone_carrier = models.CharField(max_length=2**6, blank=True, null=True)
    # Preferences. # TODO: how should this be done?
    # How to do this? Would be better to just join it to the Group.
    # TODO: Include this at all?
    coop = models.ForeignKey('Coop', related_name='coop')

    def __str__(self):
        return '{fn} at {co}'.format(fn=self.full_name,
                                     co=self.coop.short_name)

import pytz
# coop = Coop(short_name='Dudley', short_description='3 Sac and 05.',
            # time_zone=pytz.timezone('UTC'), email_prefix='[Points]')
# coop.save()
# cooper = Cooper(full_name='Alex Traub', display_name='Alex', coop=coop)
# cooper.save()

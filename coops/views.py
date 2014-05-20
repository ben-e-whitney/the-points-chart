from django.shortcuts import render

# Create your views here.

import datetime
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test, \
permission_required
from coops.models import Coop, Cooper
from chores.models import ChoreInstance

def index(response, coop_short_name=None):
    return HttpResponse('Welcome to the points chart.')

@login_required()
def all_chores(response, coop_short_name=None):
    def timedelta_in_interval(left, timedelta, right):
        '''
        Tests whether `timedelta` is contained in the half-open interval
        [`left` days, `right` days). If `left` is `None` then it is interpreted
        as ∞; similarly for `right`.
        '''
        if left is None:
            left = datetime.timedelta.min
        else:
            left = datetime.timedelta(left)
        if right is None:
            right = datetime.timedelta.max
        else:
            right = datetime.timedelta(right)
        return left <= timedelta <= right

    def day_checks(date):
        # TODO: add in weekday lookup.
        '''
        Sets flags relating to `date` that are read by the template. The actual
        formatting information is kept in a CSS file.
        '''
        now = datetime.date.today()
        difference = now-date
        flags = {'past'          : timedelta_in_interval(None, difference, 0),
                 'near_future'   : timedelta_in_interval(0, difference, 3),
                 'distant_future': timedelta_in_interval(3, difference, None)}
        return flags

    def instance_checks(instances, user):
        '''
        Sets flags relating to `instances` that are read by the template. The
        actual formatting information is kept in a CSS file.
        '''
        # TODO: determine what logic should be held here and what should be
        # kept here and what should be kept in the template. Maybe it should be
        # all here.
        # TODO: currently unused. Unsure if this level of granularity is
        # desired.
        # end_time = datetime.datetime.combine(instance.date,
                                             # instance.chore.end_time)
        flags = {
            'needs_sign_up'  : instance.signed_up  is None,
            'needs_sign_off' : instance.signed_off is None,
        }
        if not flags['needs_sign_up']:
            flags['user_signed_up'] = instance.signed_up.display_name  == \
                user.username,
            print(instance.signed_up.display_name)
            print(user.username)
            print('')
        if not flags['needs_sign_off']:
            flags['user_signed_off'] = instance.signed_off.display_name  == \
                user.username,
        # TODO: keeping this?
        # Now for properties that depend on the above.
        # flags.update({'user needs sign-off': flags['user signed up'] and \
                # not flags['has sign-off'] and flags['past']}
        return flags
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday']
    # TODO: put in error checking here or something. At least test what happens
    # when two co-ops (try to) have the same name. Maybe that is what should be
    # forbidden -- or have `coop_short_name` be more of a URL-specific thing.
    # TODO: maybe better to add a coop column to ChoreInstances? Sounds bad.
    coop = Coop.objects.get(short_name=coop_short_name)
    chore_instances = ChoreInstance.objects.filter(chore__coop=coop)
    instances_by_date = []
    for date in chore_instances.dates('date', 'day', 'ASC'):
        instances_today = chore_instances.filter(date=date)\
                          .order_by('chore__start_time', 'chore__short_name')
        instance_dicts = []
        for instance in instances_today:
            instance_dicts.append({'chore': instance,
                           'flags': instance_checks(instance, response.user)})

        # TODO: organize so that date/flag and instance/flag thing is
        # consistent. Probably instead scrap and do diagnosis thing.
        instances_by_date.append({
            'date'       : date,
            'flags'      : day_checks(date),
            'instances'  : instance_dicts,
            'weekday'    : weekdays[date.weekday()],
            'chores'     : instances_today,
         })
    # TODO: figure out how this user thing should work.
    try:
        cooper = Cooper.objects.filter(username=response.user.username)[0]
    except IndexError as e:
        cooper = None
    return render(response, 'templates/chores/all_chores.html',
                  dictionary={'coop': coop, 'cooper': cooper,
                              'chores_by_day': instances_by_date})

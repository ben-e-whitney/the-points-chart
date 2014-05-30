from django.shortcuts import render

# Create your views here.

import datetime
import json
import pytz
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test, \
permission_required
from profiles.models import UserProfile, GroupProfile
from chores.models import ChoreInstance


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
    return left <= timedelta < right

def timedelta_pretty_print(timedelta):
    # TODO: this needs testing (including edge conditions).
    pretty_print = ''
    abs_td = abs(timedelta)
    if abs_td < datetime.timedelta(seconds=60):
        pretty_print += '{num} seconds'.format(num=abs_td.seconds)
    elif abs_td < datetime.timedelta(seconds=60**2):
    # For consistency I am not using rounding for these next two. See
    # <https://docs.python.org/3/library/datetime.html#timedelta-objects>.
        pretty_print += '{num} minutes'.format(num=abs_td.seconds//60)
    elif abs_td < datetime.timedelta(days=1):
        pretty_print += '{num} hours'.format(num=abs_td.seconds//60**2)
    else:
        pretty_print += '{num} days'.format(num=abs.td.days)
    # TODO: based on this, in the description of this function we should note
    # whether it expects 'now-then' or 'then-now'.
    if timedelta >= datetime.timedelta(0):
        pretty_print += ' ago'
    else:
        pretty_print += ' from now'
    return pretty_print

def index(response):
    return HttpResponse('Welcome to the points chart.')

@login_required()
def all(response):

    def find_day_classes(date):
        '''
        Sets flags relating to `date` that are read by the template. The actual
        formatting information is kept in a CSS file.
        '''
        now = datetime.date.today()
        difference = date-now
        css_classes = {
            'past'    : timedelta_in_interval(None, difference, 0),
            'near_future'   : timedelta_in_interval(0, difference, 3),
            'distant_future': timedelta_in_interval(3, difference, None)
        }
        return ' '.join([key for key,value in css_classes.items() if value])

    def find_instance_classes(instance, user):
        # TODO: do we need to make sure that we always return at least one
        # class?
        '''
        Sets flags relating to `instances` that are read by the template. The
        actual formatting information is kept in a CSS file.
        '''
        # TODO: currently unused. Unsure if this level of granularity is
        # desired.
        # end_time = datetime.datetime.combine(instance.date,
        #                                      instance.chore.end_time)
        now = datetime.date.today()
        css_classes = {
            'needs_sign_up' : not instance.signed_up and not instance.voided,
            'needs_sign_off': instance.signed_up and not instance.signed_off \
                and not instance.voided and now > instance.date,
            'voided': instance.voided,
            'user_signed_up' : instance.who_signed_up == user,
            'user_signed_off': instance.who_signed_off == user
        }
        return ' '.join([key for key,value in css_classes.items() if value])

    def find_sign_up_sentence(instance, user):
        if not instance.signed_up:
            return None
        sentence = ''
        now = datetime.date.today()
        # TODO: try to get rid of repetition here.
        if instance.who_signed_up == user:
            sentence += 'You'
            if now <= instance.date:
                sentence += ' are'
        else:
            sentence += instance.who_signed_up.get_profile().nickname
            if now <= instance.date:
                sentence += ' is'
        sentence += ' signed up.'
        return sentence

    def find_sign_off_sentence(instance, user):
        if not instance.signed_off:
            # If in addition it is the user who has signed off, we will display
            # a sentence reminding the user to get someone to sign off.
            # Currently this sentence is in the template. Could move it to this
            # file, though we've probably have to introduce some new stuff.
            # TODO: figure out how to do this cleanly. Maybe we just need to
            # introduce a flag/class for 'not signed off, but it's today so we
            # don't need one yet.'
            return ''
            # return None
        return '{nam} signed off.'.format(nam='You'
            if instance.who_signed_off == user else
            instance.who_signed_off.get_profile().nickname)

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday']
    # TODO: put in error checking here or something. At least test what happens
    # when two co-ops (try to) have the same name. Maybe that is what should be
    # forbidden -- or have `coop_short_name` be more of a URL-specific thing.
    # TODO: maybe better to add a coop column to ChoreInstance? Sounds bad.
    # Here we assume that a User is a member of only one Group. TODO: is this
    # going to make points stewards/presidents ugly? Could address this by
    # adding something in the UserProfile that points to the Group that is a
    # co-op.
    coop = response.user.get_profile().coop
    chore_instances = ChoreInstance.objects.filter(chore__coop=coop)
    instances_by_date = []
    for date in chore_instances.dates('date', 'day', 'ASC'):
        instances_today = chore_instances.filter(date=date)\
                          .order_by('chore__start_time', 'chore__short_name')
        instance_dicts = []
        for instance in instances_today:
            instance_dicts.append({
                'chore': instance,
                'class': find_instance_classes(instance, response.user),
                'sign_up_sentence' : find_sign_up_sentence(instance,
                                                           response.user),
                'sign_off_sentence': find_sign_off_sentence(instance,
                                                            response.user)
            })

        instances_by_date.append({
            'date'     : date,
            'class'    : find_day_classes(date),
            'instances': instance_dicts,
            'weekday'  : weekdays[date.weekday()],
         })
    return render(response, 'chores/all_chores.html',
                  dictionary={'coop': coop, 'cooper': response.user,
                              'chores_by_day': instances_by_date})

@login_required()
def me(response):
    all_instances = ChoreInstance.objects.filter(chore__coop=
                                 response.user.get_profile().coop)
    user_signed_up = all_instances.filter(who_signed_up=response.user)
    points_signed_up = sum(map(lambda x: x['chore__point_value'],
                               user_signed_up.values('chore__point_value')))
    return render(response, 'chores/me_chores.html',
                  dictionary={'total_signed_up': points_signed_up})

@login_required()
def sign_up(response, instance_id):
    print('In sign_up view.')
    instance = ChoreInstance.objects.get(pk=instance_id)
    if instance.signed_up:
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        # TODO: this code is very close to the stuff used in the sign_off
        # function. Make a separate function.
        # TODO: after making timezone stuff work here make those changes
        # everywhere else.
        return HttpResponse('', reason='{coo} signed up for this chore {tdp}.'\
            .format(coo=instance.who_signed_up.get_profile().nickname, tdp=\
                timedelta_pretty_print(datetime.datetime.now(pytz.utc)-\
                    instance.when_signed_up)), status=403)
    else:
        instance.who_signed_up = response.user
        instance.signed_up = True
        instance.when_signed_up = datetime.datetime.now()
        instance.save()
        # TODO: some repetition here with the chores templates. How to fix?
        # TODO: only use "Sign-off needed!" if we're in the past?
    return HttpResponse(json.dumps({'sign_up_sentence': 'You are signed up.',
        'sign_off_sentence': 'Sign-off needed!'}), status=200)

@login_required()
def sign_off(response, instance_id):
    print('In sign_off view.')
    instance = ChoreInstance.objects.get(pk=instance_id)
    if not instance.signed_up:
        # Error: no one has signed up. User should only be able to get here my
        # manually entering a URL.
        return HttpResponse('', reason='No one has signed up for this chore.',
                            status=403)
    if instance.signed_off:
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        return HttpResponse('', reason='{coo} signed off on this chore {tdp}.'\
            .format(coo=instance.who_signed_off.get_profile().nickname, tpd=\
                timedelta_pretty_print(datetime.datetime.now()-\
                    instance.when_signed_off)), status=403)
    if instance.who_signed_up == response.user:
        # Error: can't sign off on your own chore. Have this pop up in an
        # alert.
        return HttpResponse('', reason="You can't sign off on your own "
                            "chore.", status=403)
    else:
        instance.who_signed_off = response.user
        instance.signed_off = True
        instance.when_signed_off = datetime.datetime.now()
        instance.save()
        return HttpResponse(json.dumps({
            'sign_off_sentence': 'You signed off.'}), status=200)

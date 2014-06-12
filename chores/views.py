from django.shortcuts import render

# Create your views here.

import datetime
import json
import pytz
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test, \
permission_required
from django.contrib.auth.models import User
from django.template import loader, Context
from profiles.models import UserProfile, GroupProfile
from chores.models import Chore


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

    def find_chore_classes(chore, user):
        # TODO: do we need to make sure that we always return at least one
        # class?
        '''
        Sets flags relating to `chores` that are read by the template. The
        actual formatting information is kept in a CSS file.
        '''
        # TODO: currently unused. Unsure if this level of granularity is
        # desired.
        # end_time = datetime.datetime.combine(chore.start_date,
        #                                      chore.end_time)
        now = datetime.date.today()
        css_classes = {
            'needs_sign_up' : not chore.signed_up and not chore.voided,
            'needs_sign_off': chore.signed_up and not chore.signed_off \
                and not chore.voided and now > chore.start_date,
            'voided': chore.voided,
            'user_signed_up' : user == chore.signed_up.who,
            'user_signed_off': user == chore.signed_off.who
        }
        return ' '.join([key for key,value in css_classes.items() if value])

    def find_sign_up_sentence(chore, user):
        if not chore.signed_up:
            return None
        sentence = ''
        now = datetime.date.today()
        # TODO: try to get rid of repetition here.
        if user == chore.signed_up.who:
            sentence += 'You'
            if now <= chore.start_date:
                sentence += ' are'
        else:
            sentence += chore.signed_up.who.profile.nickname
            if now <= chore.start_date:
                sentence += ' is'
        sentence += ' signed up.'
        return sentence

    def find_sign_off_sentence(chore, user):
        if not chore.signed_off:
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
            if user == chore.signed_off.who else
            chore.signed_off.who.profile.nickname)

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday']
    # TODO: put in error checking here or something. At least test what happens
    # when two co-ops (try to) have the same name. Maybe that is what should be
    # forbidden -- or have `coop_short_name` be more of a URL-specific thing.
    # Here we assume that a User is a member of only one Group. TODO: is this
    # going to make points stewards/presidents ugly? Could address this by
    # adding something in the UserProfile that points to the Group that is a
    # co-op.
    coop = response.user.profile.coop
    chores = Chore.objects.filter(skeleton__coop=coop)
    chores_by_date = []
    for date in chores.dates('start_date', 'day', 'ASC'):
        chores_today = chores.filter(start_date=date)\
                          .order_by('skeleton__start_time',
                                    'skeleton__short_name')
        chore_dicts = []
        for chore in chores_today:
            chore_dicts.append({
                'chore': chore,
                'class': find_chore_classes(chore, response.user),
                'sign_up_sentence' : find_sign_up_sentence(chore,
                                                           response.user),
                'sign_off_sentence': find_sign_off_sentence(chore,
                                                            response.user)
            })

        chores_by_date.append({
            'date'    : date,
            'class'   : find_day_classes(date),
            'schedule': chore_dicts,
            'weekday' : weekdays[date.weekday()],
         })
    return render(response, 'chores/all.html',
                  dictionary={'coop': coop, 'cooper': response.user,
                              'days': chores_by_date})

@login_required()
def me(response):
    # TODO: most of this into another function so it can be used in making a
    # chart that the points steward can look at.
    def sum_point_values(chores):
        '''
        Returns the sum of the point values of the chores in `chores`.
        '''
        return sum(map(lambda x: x['skeleton__point_value'],
                       chores.values('skeleton__point_value')))

    coop = response.user.profile.coop
    upcoming_lower_boundary = datetime.date.today()
    # TODO: here and elsewhere, make values like the '3' here either variables
    # or function arguments.
    upcoming_upper_boundary = upcoming_lower_boundary+\
        datetime.timedelta(days=3)

    all_chores = Chore.objects.filter(skeleton__coop=coop)
    my_chores = all_chores.filter(signed_up__who=response.user)
    my_upcoming_chores = my_chores.filter(
        start_date__gte=upcoming_lower_boundary,
        start_date__lte=upcoming_upper_boundary).order_by('start_date')
    my_chores_needing_sign_off = my_chores.filter(
        start_date__lt=upcoming_lower_boundary, voided=False,
        signed_off=False).order_by('start_date')
    points_signed_up = sum_point_values(my_chores)
    points_needing_sign_off = sum_point_values(my_chores_needing_sign_off)
    return render(response, 'chores/me.html',
                  dictionary={
                      'coop': coop,
                      'total_signed_up': points_signed_up,
                      'total_needing_sign_off': points_needing_sign_off,
                      'upcoming_chores': my_upcoming_chores,
                      'chores_needing_sign_off':
                          my_chores_needing_sign_off,
                  })

@login_required()
def sign_up(response, chore_id):
    print('In sign_up view.')
    chore = Chore.objects.get(pk=chore_id)
    if chore.signed_up:
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        # TODO: this code is very close to the stuff used in the sign_off
        # function. Make a separate function.
        # TODO: after making timezone stuff work here make those changes
        # everywhere else.
        return HttpResponse('', reason='{coo} signed up for this chore {tdp}.'\
            .format(coo=chore.signed_up.who.profile.nickname, tdp=\
                timedelta_pretty_print(datetime.datetime.now(pytz.utc)-\
                    chore.when_signed_up)), status=403)
    else:
        chore.signed_up.who = response.user
        chore.signed_up = True
        chore.when_signed_up = datetime.datetime.now()
        chore.save()
        # TODO: some repetition here with the chores templates. How to fix?
        # TODO: only use "Sign-off needed!" if we're in the past?
    return HttpResponse(json.dumps({'sign_up_sentence': 'You are signed up.',
        'sign_off_sentence': 'Sign-off needed!'}), status=200)

@login_required()
def sign_off(response, chore_id):
    print('In sign_off view.')
    chore = Chore.objects.get(pk=chore_id)
    if not chore.signed_up:
        # Error: no one has signed up. User should only be able to get here my
        # manually entering a URL.
        return HttpResponse('', reason='No one has signed up for this chore.',
                            status=403)
    if chore.signed_off:
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        return HttpResponse('', reason='{coo} signed off on this chore {tdp}.'\
            .format(coo=chore.who_signed_off.profile.nickname, tpd=\
                timedelta_pretty_print(datetime.datetime.now()-\
                    chore.when_signed_off)), status=403)
    if response.user == chore.signed_up.who:
        # Error: can't sign off on your own chore. Have this pop up in an
        # alert.
        return HttpResponse('', reason="You can't sign off on your own "
                            "chore.", status=403)
    else:
        chore.who_signed_off = response.user
        chore.signed_off = True
        chore.when_signed_off = datetime.datetime.now()
        chore.save()
        return HttpResponse(json.dumps({
            'sign_off_sentence': 'You signed off.'}), status=200)

def create_calendar(response, username):
    # Test to see if that user wants a public calendar. Also do error checking
    # with this next step.
    user = User.objects.get(username=username)
    chores = Chore.objects.filter(signed_up__who=user)
    coop = user.profile.coop
    response = HttpResponse(content_type='text/calendar')
    response['Content-Disposition'] = ('attachment; '
        'filename="{sho}_chore_calendar.ics"'.format(
            sho=coop.profile.short_name.replace(' ', '_')))
    template = loader.get_template('calendars/calendar.ics')
    context = Context({'coop': coop, 'chores': chores})
    response.write(template.render(context))
    return response

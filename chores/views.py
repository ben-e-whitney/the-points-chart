from django.shortcuts import render

# Create your views here.

import datetime
import json
import pytz
import itertools

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test, \
permission_required
from django.contrib.auth.models import User
from django.template import loader, Context

from chores.models import Chore
from profiles.models import UserProfile, GroupProfile
from stewardships.models import StewardshipSkeleton, Stewardship, Absence, \
    ShareChange


# TODO: put extra functions and lengthy variable definitions in another file.
# TODO: name needs improving here.
def sum_chores(chores):
    '''
    Returns the sum of the point values of the chores in `chores` and a string
containing all their names.
    '''
    return {'total': sum(map(lambda x: x['skeleton__point_value'],
                             chores.values('skeleton__point_value'))),
            'concatenated_items': ', '.join(map(str, chores))}

def get_obligations(user, coop=None):

    def update(dict_, key, data, mode):

        '''
        Construct and update a dictionary of dictionaries piece-by-piece.

        Arguments:
            dict_ -- Data structure being modified.
            key   -- Identifies the entry to create or change.
            data  -- Used to changing the entry.
            mode  -- Dictates how `data` will be used to change the entry.
        '''

        def appender(dict_, key, data):
            dict_[key]['items'].append(data)
            dict_[key]['html_titles'].append(', '.join(str(chore) for chore in
                                                       data))
            return dict_

        def combiner(dict_, key, data):
            # TODO: this seems to be the wrong way to go about it.
            dict_[key]['items'] += list(data)
            return dict_

        options_by_mode = {
            'append': {
                'blank_entry': {'title': None, 'items': [], 'html_titles': []},
                'updater': appender
            },
            'combine': {
                'blank_entry': {'title': None, 'items': []},
                'updater': combiner
            }
        }
        try:
            options = options_by_mode[mode]
        except KeyError as e:
            raise KeyError('Unrecognized mode {mod}.'.format(mod=mode))

        if not key in dict_.keys():
            dict_[key] = options['blank_entry']
            dict_[key]['title'] = key
            return update(dict_, key, data, mode)
        else:
            return options['updater'](dict_, key, data)

    if coop is None:
        coop = user.profile.coop
    # TODO: Still don't like how this is being done. Like the idea of making
    # repositories and only later organizing them by section, but that's
    # complicated by needing multiple subsections (e.g. 'Voided') both
    # 'appended' and 'combined'.
    list_structure = {
        'sections': ['Chores', 'Stewardships and Similar', 'Benefit Changes'],
        'subsections': [['Upcoming', 'Voided', 'Needing Sign Off'],
                        ['Stewardships', 'Special Points', 'Loans'],
                        ['Absences', 'Share Changes']]
    }
    table_structure = {
        'sections': ['Summary', 'Chores', 'Stewardships and Similar'],
        'subsections': [['Load', 'Credits', 'Balance'],
                        ['Signed Up', 'Signed Off', 'Needing Sign Off',
                         'Voided'],
                        ['Stewardships', 'Special Points', 'Loans']]
    }
    list_stats = {}
    table_stats = {}

    cycle_boundaries = []
    signed_args = [coop, cycle_start, cycle_stop]
    categories = {
        'all chores': 
    cycles = []
    # TODO: first pull out all the chores, and only then filter by date.
    for cycle_num, cycle_start, cycle_stop in coop.profile.cycles():
        cycles.append({'cycle_num': cycle_num, 'cycle_start': cycle_start,
                       'cycle_stop': cycle_stop})
        # TODO: could make a big method in the custom Manager that returns all
        # of these as a dictionary. That would be very nice. Think of how to
        # make it efficient if you want to query it multiple times.
        signed_args = [coop, cycle_start, cycle_stop]
        my_chores = Chore.objects.signed(
            *signed_args,
            signatures=['signed_up'],
            users=[user]
        )
        upcoming_lower_boundary = datetime.date.today()
        upcoming_upper_boundary = upcoming_lower_boundary+\
                datetime.timedelta(days=coop.profile.release_buffer)
        my_chores_upcoming = Chore.objects.signed(coop,
            upcoming_upper_boundary, upcoming_upper_boundary,
            signatures=['signed_up'], users=[user])
        # TODO: this is inefficient. Maybe need to subclass QueryObject to add
        # in ability to filter by truth value of the Signatures?
        my_chores_voided = Chore.objects.signed(
            *signed_args,
            signatures = ['signed_up', 'voided'],
            users = [user, None],
            desired_booleans = [True, False]
        )
        my_chores_signed_off = Chore.objects.signed(
            *signed_args,
            signatures = ['signed_up', 'voided', 'signed_off'],
            users = [user, None, None],
            desired_booleans = [True, False, True]
        )
        # TODO: originally we had this filtering by the start_date being less than
        # the current date. If we drop the assumption that chores have the same
        # stop and start date, that isn't what's going on here. Also there is the
        # issue of less than versus less than or equal to. Hopefully can fix this
        # by allowing us to use `signed` on QueryObjects.
        my_chores_needing_sign_off = Chore.objects.signed(
            coop,
            cycle_start,
            datetime.date.today(),
            signatures = ['signed_up', 'voided', 'signed_off'],
            users = [user, None, None],
            desired_booleans = [True, False, False]
        )

        # Be careful here. I'm specifying that these things shouldn't be voided
        # just for clarity. Right now they never should be voided. If that's added
        # in, this will need to be inspected a bit more closely.
        my_stewardships_all = Stewardship.objects.signed(
            *signed_args,
            signatures=['signed_up'],
            users=[user]
        )
        # TODO: can bring back something like this when the methods work with
        # QueryObjects.
        # my_classical_stewardships = my_stewardships_all.filter(
            # skeleton__category=StewardshipSkeleton.STEWARDSHIP)
        # my_special_points = my_stewardships_all.filter(
            # skeleton__category=StewardshipSkeleton.SPECIAL_POINTS)
        # my_loans = my_stewardships_all.filter(
            # skeleton__category=StewardshipSkeleton.LOAN)
        my_classical_stewardships = [stew for stew in my_stewardships_all if
            stew.skeleton.category == StewardshipSkeleton.STEWARDSHIP]
        my_special_points = [stew for stew in my_stewardships_all if
            stew.skeleton.category == StewardshipSkeleton.SPECIAL_POINTS]
        my_loans = [stew for stew in my_stewardships_all if
            stew.skeleton.category == StewardshipSkeleton.LOAN]

        my_absences = Absence.objects.signed(
            *signed_args,
            signatures=['signed_up'],
            users=[user]
        )

        my_absences = Absence.objects.signed(
            *signed_args,
            signatures=['signed_up'],
            users=[user]
        )
        my_share_changes = ShareChange.objects.signed(
            *signed_args,
            signatures=['signed_up'],
            users=[user]
        )
        my_accounts = transpose(calculate_loads(user, coop=coop))
        list_datas = [my_chores_upcoming, my_chores_voided,
                      my_chores_needing_sign_off, my_classical_stewardships,
                      my_special_points, my_loans, my_absences,
                      my_share_changes]
        table_datas = [my_accounts['load'], my_accounts['credits'],
                       my_accounts['balance'], my_chores, my_chores_signed_off,
                       my_chores_needing_sign_off, my_chores_voided,
                       my_classical_stewardships, my_special_points, my_loans]
        # TODO: hopefully in rewriting the above you get rid of this repeated
        # code, here and further below.
        for key, data in zip(itertools.chain(*list_structure['subsections']),
                             list_datas):
            list_stats = update(list_stats, key, data, 'combine')
        for key, data in zip(itertools.chain(*table_structure['subsections']),
                                             table_datas):
            table_stats = update(table_stats, key, data, 'append')
    list_information = []
    table_information = []
    for i, section in enumerate(list_structure['sections']):
        list_information.append({'title': section, 'sections': []})
        for subsection in list_structure['subsections'][i]:
            list_information[i]['sections'].append({
                'title': subsection,
                'items': list_stats[subsection]['items'],
            })
    for i, section in enumerate(table_structure['sections']):
        table_information.append({'title': section, 'sections': []})
        for subsection in table_structure['subsections'][i]:
            table_information[i]['sections'].append({
                'title': subsection,
                'items': table_stats[subsection]['items'],
                'html_titles': table_stats[subsection]['html_titles']
            })
    return {'list_information': list_information,
            'table_information': table_information,
            'cycles': cycles}
    # table_structure = {
        # 'sections': ['Summary', 'Chores', 'Stewardships and Similar'],
        # 'subsections': [['Load', 'Credits', 'Balance'],
                        # ['Signed Up', 'Signed Off', 'Needing Sign Off',
                         # 'Voided'],
                        # ['Stewardships', 'Special Points', 'Loans']]
    # }

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

# TODO: also include here what the load should be. For this we will
# need a load calculator. Maybe not even a separate function since
# we've already done so much of the work here.
def calculate_loads(user, coop=None):
    if coop is None:
        coop = user.profile.coop
    # Storing as a tuple so we can iterate over it multiple times.
    coopers = tuple(User.objects.filter(profile__coop=coop))
    subtotals = []
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        load = 0
        signed_up = 0
        completed = 0
        signed_args = [coop, start_date, stop_date]
        chores = Chore.objects.signed(
            *signed_args,
            signatures=['voided'],
            desired_booleans=[False]
        )
        stewardships = Stewardship.objects.signed(
            *signed_args,
            signatures=['voided'],
            desired_booleans=[False]
        )
        absences = Absence.objects.signed(
            *signed_args,
            signatures=['voided'],
            desired_booleans=[False]
        )
        share_changes = ShareChange.objects.signed(
            *signed_args,
            signatures=['voided'],
            desired_booleans=[False]
        )
        # TODO: how should this be done?
        total_points = sum(map(lambda x: x.skeleton__point_value,
                               itertools.chain(chores, stewardships)))
        total_presence = -sum(map(lambda x: x.days_gone, absences))
        total_share = sum(map(lambda x: x.share_change, share_changes))
        # TODO: put this in a function?
        for cooper in coopers:
            total_presence += cooper.profile.presence
            total_share += cooper.profile.share
        # TODO: what really seems to be missing here is being able to use the
        # `signed` method on a QuerySet. There is a way to do this -- look it
        # up if you decide to go this route.
        signed_up = sum(
            map(lambda x: x.skeleton__point_value,
                Chore.objects.signed(
                    *signed_args,
                    signatures=['voided', 'signed_up'],
                    desired_booleans=[False, True],
                    users= [None, user])
           ))
        completed = sum(
            map(lambda x: x.skeleton__point_value,
                Chore.objects.signed(
                    *signed_args,
                    signatures=['voided', 'signed_up', 'signed_off'],
                    desired_booleans=[False, True, True],
                    users= [None, user, None])
           ))
        points_per_day_share = total_points/(total_presence*total_share)
        load = points_per_day_share*user.profile.presence*user.profile.share
        subtotals.append({'load': load, 'signed_up': signed_up,
                         'completed': completed})
    accounts = []
    old_balance = 0
    for i, subtotal in enumerate(subtotals):
        load = subtotal['load']
        credits = subtotal['completed' if i < len(subtotals)-1 else
                           'signed_up']
        balance = old_balance+credits-load
        accounts.append({'load': load, 'credits': credits,
                         'balance': balance})
        old_balance = balance
    return accounts

def index(response):
    return HttpResponse('Welcome to the points chart.')

@login_required()
def all_users(response):

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
    # TODO: here also sort by cycle?
    return render(response, 'chores/all.html',
                  dictionary={'coop': coop, 'cooper': response.user,
                              'days': chores_by_date})

# TODO: write a function/URL thing for when they go to 'chores/me/'.
# TODO: this should now require permissions.
@login_required()
def one_user(response, username):
    user = User.objects.get(username=username)
    coop = user.profile.coop
    obligations = get_obligations(user, coop=coop)
    cycles = obligations['cycles']
    list_information = obligations['list_information']
    table_information = obligations['table_information']
    for x in table_information:
        print(x)
        print('')
    render_dictionary = {
        'coop': coop,
        'cooper': user,
        'list_information': list_information,
        'table_information': table_information,
        'point_cycles': cycles
    }
    return render(response, 'chores/me.html', dictionary=render_dictionary)

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

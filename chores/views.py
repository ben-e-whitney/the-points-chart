from django.shortcuts import render

# Create your views here.

import datetime
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

def calculate_point_sum(chores):
    return sum(chore.skeleton.point_value for chore in chores)

def make_html_title(chores):
    return ', '.join(str(chore) for chore in chores)

# TODO: put extra functions and lengthy variable definitions in another file.
# TODO: name needs improving here.

# TODO: think I can get rid of this. Currently using this is a sign that you
# are using the wrong data set.
# def unique(list_):
    # already_seen = set(())
    # unique_list = []
    # for item in list_:
        # if item not in already_seen:
            # unique_list.append(item)
            # already_seen.add(item)
    # return unique_list

class DisplayInformation():
    def __init__(self, name, structure, keys, processor, format_key):
        self.name = name
        self.structure = structure
        self.keys = keys
        self.processor = processor
        self.format_key = format_key
        # TODO: put futher checks here? That or document what structure you're
        # expecting to get.
        # TODO: get rid of this temporary stuff.

        try:
            assert sum(len(section_subsections) for section_subsections in
                       self.structure['subsections']) == len(self.keys)
        except AssertionError as e:
            # raise AssertionError(
                # sum(len(section_subsections) for section_subsections in
                       # self.structure['subsections']), len(self.keys)
            # )
            raise AssertionError(
                self.structure['subsections'], self.keys
            )

    def load_data(self, data):
        self.data = {
            key: (data[key][self.format_key] if self.format_key is not None
                  else data[key]) for key in self.keys
        }

    # TODO: document this or whatever. Figure out the right way.
    def process_data(self):
        # TODO: at the beginning have it just take these in.
        self.data = {
            key: self.processor(item) for key, item in
            self.data.items()
        }

    def populate_structure(self):
        self.structured_data = []
        key_index = 0
        for i, section in enumerate(self.structure['sections']):
            self.structured_data.append({'title': section, 'sections': []})
            # Assuming this is only called once, so that the dictionary we just
            # appended is located at index `i`.
            for subsection in self.structure['subsections'][i]:
                self.structured_data[i]['sections'].append(
                    {
                        'title': subsection,
                        'dictionaries': [
                            dict_ for dict_ in self.data[self.keys[key_index]]
                        ]
                    }
                )
                key_index += 1

    def purge_empty(self):
        # list/dict ('sections')/list/dict ('dictionaries')
        # test if *that* is [] or whatever
        # Filter subsections.
        for big_dict in self.structured_data:
            # Using mutability/fact that `self.structured_data` stores
            # references to objects.
            big_dict['sections'] = [item for item in big_dict['sections'] if
                                    item['dictionaries']]
        # Filter sections.
        self.structured_data = [big_dict for big_dict in self.structured_data
                                if big_dict['sections']]
        return None

    def create_template_data(self, data):
        self.load_data(data)
        self.process_data()
        self.populate_structure()
        self.purge_empty()
        return self.structured_data

def get_obligations(user, coop=None):

    if coop is None:
        coop = user.profile.coop

    upcoming_lower_boundary = datetime.date.today()
    upcoming_upper_boundary = upcoming_lower_boundary+\
            datetime.timedelta(days=coop.profile.release_buffer)
    all_chores = Chore.objects.for_coop(coop).signed_up(user, True)
    all_stewardships = Stewardship.objects.for_coop(coop).signed_up(
        user, True)
    data = {
        'all chores': all_chores,
        'upcoming chores': all_chores.in_window(upcoming_lower_boundary,
                                                upcoming_upper_boundary),
        'voided': all_chores.voided(user, True),
        'signed off': all_chores.signed_off(user, True),
        'not signed off': all_chores.signed_off(user, False),
        'all stewardships': all_stewardships,
        # TODO: could new QuerySets/models/whatever in for these.
        'stewardships': all_stewardships.filter(
            skeleton__category=StewardshipSkeleton.STEWARDSHIP),
        'special points': all_stewardships.filter(
            skeleton__category=StewardshipSkeleton.SPECIAL_POINTS),
        'loans': all_stewardships.filter(
            skeleton__category=StewardshipSkeleton.LOAN),
        'absences': Absence.objects.signed_up(user, True),
        'share changes': ShareChange.objects.signed_up(user, True)
    }
    data['ready for signature'] = data['not signed off'].filter(
        start_date__lte=datetime.date.today())
    # Rearranging.
    for key, item in data.items():
        data[key] = {'original': item, 'per cycle': []}
    cycles = []
    accounts = []
    for cycle_num, cycle_start, cycle_stop in coop.profile.cycles():
        cycles.append({'cycle_num': cycle_num, 'cycle_start': cycle_start,
                       'cycle_stop': cycle_stop})
        for key in data:
            data[key]['per cycle'].append(
                data[key]['original'].in_window(cycle_start, cycle_stop)
            )
    # Rearranging again.
    data.update(calculate_loads(user, coop=coop))

    def list_processor(items):
        return [
            {'items': item} for item in items if item
        ]

    def table_processor(items):
        return [
            {'value': calculate_point_sum(chores),
             'html_title': make_html_title(chores)}
            for chores in items
        ]

    display_infos = [
        DisplayInformation('list_information', {
                'sections': ['Chores', 'Stewardships and Similar',
                             'Benefit Changes'],
                'subsections': [['Upcoming', 'Voided', 'Ready for Signature'],
                                ['Stewardships', 'Special Points', 'Loans'],
                                ['Absences', 'Share Changes']]
            }, [
                'upcoming chores', 'voided', 'ready for signature',
                'stewardships', 'special points', 'loans', 'absences',
                'share changes'
            ], list_processor, 'original'),
        DisplayInformation('table_information', {
                'sections': ['Chores', 'Stewardships and Similar'],
                'subsections': [['Signed Up', 'Signed Off', 'Needing Sign Off',
                                 'Voided'],
                                ['Stewardships', 'Special Points', 'Loans']]
            }, [
                'all chores', 'signed off', 'not signed off', 'voided',
                'stewardships', 'special points', 'loans'
            ], table_processor, 'per cycle'),
        DisplayInformation('summary_information', {
                'sections': ['Summary'],
                'subsections': [['Load', 'Credits', 'Balance']]
            }, [
                'loads', 'credits', 'balances'
            ], list_processor, None)
    ]
    dict_to_return = {
        display_info.name: display_info.create_template_data(data) for
        display_info in display_infos
    }
    dict_to_return.update({'point_cycles': cycles})
    return dict_to_return

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

def calculate_loads(user, coop=None):
    if coop is None:
        coop = user.profile.coop
    # Storing as a tuple so we can iterate over it multiple times.
    coopers = tuple(User.objects.filter(profile__coop=coop))
    subtotals = []
    # Note that we're not checking whether stewardships are voided or not
    # (since currently that doesn't happen/has no meaning/effect). Maybe
    # should be changed (TODO).
    data = {
        'chores': Chore.objects.for_coop(coop).voided(None, False),
        'stewardships': Stewardship.objects.for_coop(coop),
        'absences': Absence.objects.for_coop(coop),
        'share changes': ShareChange.objects.for_coop(coop)
    }
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        load = 0
        signed_up = 0
        completed = 0

        adds_to_points = itertools.chain(
            data['chores'].in_window(start_date, stop_date),
            data['stewardships'].in_window(start_date, stop_date)
        )
        adds_to_presence = data['absences'].in_window(start_date, stop_date)
        adds_to_share = data['share changes'].in_window(start_date, stop_date)
        total_points = sum(map(lambda x: x.skeleton.point_value,
                               adds_to_points))
        total_presence = -sum(map(lambda x: x.days_gone, adds_to_presence))
        total_share = sum(map(lambda x: x.share_change, adds_to_share))
        for cooper in coopers:
            total_presence += cooper.profile.presence
            total_share += cooper.profile.share
        signed_up = sum(
            map(lambda x: x.skeleton.point_value,
                data['chores'].signed_up(user, True)
           ))
        completed = sum(
            map(lambda x: x.skeleton.point_value,
                data['chores'].signed_up(user, True).signed_off(None, True)
           ))
        points_per_day_share = total_points/(total_presence*total_share)
        load = points_per_day_share*user.profile.presence*user.profile.share
        subtotals.append({'load': load, 'signed_up': signed_up,
                         'completed': completed})
    accounts = {'loads': [], 'credits': [], 'balances': []}
    old_balance = 0
    for i, subtotal in enumerate(subtotals):
        load = subtotal['load']
        credits = subtotal['completed' if i < len(subtotals)-1 else
                           'signed_up']
        balance = old_balance+credits-load
        accounts['loads'].append(load)
        accounts['credits'].append(credits)
        accounts['balances'].append(balance)
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
    chores = Chore.objects.for_coop(coop)
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
    render_dictionary = {
        'coop': coop,
        'cooper': user,
    }
    render_dictionary.update(get_obligations(user, coop=coop))
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

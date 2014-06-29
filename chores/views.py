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

class DisplayInformation():
    def __init__(self, name, structure, keys, processor, format_key):
        self.name = name
        self.structure = structure
        self.keys = keys
        self.processor = processor
        self.format_key = format_key
        # TODO: put futher checks here? That or document what structure you're
        # expecting to get.
        try:
            assert sum(len(section_subsections) for section_subsections in
                       self.structure['subsections']) == len(self.keys)
        except AssertionError as e:
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
    upcoming_upper_boundary = (upcoming_lower_boundary+
            datetime.timedelta(days=coop.profile.release_buffer))
    all_chores = Chore.objects.for_coop(coop).signed_up(user, True)
    all_stewardships = Stewardship.objects.for_coop(coop).signed_up(
        user, True)
    data = {
        'all chores': all_chores,
        'upcoming chores': all_chores.in_window(upcoming_lower_boundary,
                                                upcoming_upper_boundary),
        # For these next three it doesn't matter who has (or hasn't) signed.
        # off. Putting no checks for validity here.
        'voided': all_chores.voided(None, True),
        'signed off': all_chores.signed_off(None, True),
        'not signed off': all_chores.signed_off(None, False),
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

# TODO: another option (attractive) would be to put all of this as methods of
# the Signature model. I think we would want to subclass that class, but all
# for the sake of including some view logic in the model? Not sure what is the
# best course.
class ChoreSentence():
    chore_attribute = None
    past_participle = None
    adjectival_phrase = None
    button_action_text = None
    button_reversion_text = None
    JavaScript_action_function = None
    JavaScript_reversion_function = None
    action_permission_attribute = None
    reversion_permission_attribute = None
    # Attributes used for the JSON dict. Need to have fallback values.
    identifier = None
    button = None
    button_text = None
    report = None
    report_text = None
    JavaScript_function = None

    # TODO: just stripped out premature optimization with caching the current
    # date/datetime. Can reinsert if needed.
    def __init__(self, user, chore, chore_attribute=None):
        if chore_attribute is not None:
            self.chore_attribute = chore_attribute
        # Otherwise use the class attribute.
        self.current_datetime = datetime.datetime.now()
        self.current_date = self.current_datetime.date()
        self.user = user
        self.chore = chore
        self.signature = getattr(self.chore, self.chore_attribute)
        self.owner = self.signature.who
        self.identifier = self.chore_attribute
        self.get_button()
        self.get_report()

    def action_permitted(self):
        return getattr(self.chore, self.action_permission_attribute)(
            self.user)['boolean']

    def reversion_permitted(self):
        return getattr(self.chore, self.reversion_permission_attribute)(
            self.user)['boolean']

    def get_button(self):
        if self.action_permitted():
            self.button = True
            self.JavaScript_function = self.JavaScript_action_function
            self.button_text = self.button_action_text
        else:
            if self.reversion_permitted():
                self.button = True
                self.JavaScript_function = self.JavaScript_reversion_function
                self.button_text = self.button_reversion_text
            else:
                self.button = False

    def current_report_text(self):
        return '{beg} {end}.'.format(
            beg='You are' if self.owner == self.user else '{nam} is'.format(
                nam=self.owner.profile.nickname),
            end=self.adjectival_phrase)

    def past_report_text(self):
        return '{nam} {vpp}.'.format(nam='You' if self.owner == self.user else
            self.owner.profile.nickname, vpp=self.past_participle)

    def get_report(self):
        # TODO: worth an `in_the_future`-style method for this? Or give that
        # method an option or something?
        self.report = self.signature
        if self.report:
            if self.current_date <= self.chore.start_date:
                self.report_text = self.current_report_text()
            else:
                self.report_text = self.past_report_text()
        else:
            self.report_text = None

    def dict_for_json(self):
        return {
            'identifier': self.identifier,
            'button': self.button,
            'button_text': self.button_text,
            # Need to explicity convert to Boolean here so that JSON doesn't
            # complain when it is dealt a Signature. For now this is not
            # necessary with `self.button`.
            'report': bool(self.report),
            'report_text': self.report_text,
            'JavaScript_function': self.JavaScript_function
        }

class VoidSentence(ChoreSentence):
    chore_attribute = 'voided'
    past_participle = 'voided'
    button_action_text = 'Void'
    button_reversion_text = 'Revert Void'
    # Remember that `void` is a JavaScript operator.
    JavaScript_action_function = 'voidChore'
    JavaScript_reversion_function = 'revertVoidChore'
    action_permission_attribute = 'void_permission'
    reversion_permission_attribute = 'revert_void_permission'

    def current_report_text(self):
        return '{nam} {vpp}.'.format(
            nam='You' if self.owner == self.user else
                self.owner.profile.nickname,
            vpp=self.past_participle)

    past_report_text = current_report_text

class SignUpSentence(ChoreSentence):
    chore_attribute = 'signed_up'
    past_participle = 'signed up'
    adjectival_phrase = 'signed up'
    button_action_text = 'Sign Up'
    button_reversion_text = 'Revert Sign-Up'
    JavaScript_action_function = 'signUpChore'
    JavaScript_reversion_function = 'revertSignUpChore'
    action_permission_attribute = 'sign_up_permission'
    reversion_permission_attribute = 'revert_sign_up_permission'

class SignOffSentence(ChoreSentence):
    chore_attribute = 'signed_off'
    past_participle = 'signed off'
    adjectival_phrase = 'signed off'
    button_action_text = 'Sign Off'
    button_reversion_text = 'Revert Sign-Off'
    JavaScript_action_function = 'signOffChore'
    JavaScript_reversion_function = 'revertSignOffChore'
    action_permission_attribute = 'sign_off_permission'
    reversion_permission_attribute = 'revert_sign_off_permission'

def get_chore_sentences(user, chore):
    return [
        SignUpSentence(user, chore),
        SignOffSentence(user, chore),
        VoidSentence(user, chore)
    ]

# TODO: use an id (or something else?) to make it open to the current day.
@login_required()
def all_users(response):

    def find_day_id(date):
        now = datetime.date.today()
        if date == now:
            return 'today'
        else:
            return ''

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
            # TODO: could make some sort of `sentence_args` and
            # `sentence_kwargs` variables to feed into these.
            chore_dicts.append({
                'chore': chore,
                'class': chore.find_CSS_classes(response.user),
                'sentences': get_chore_sentences(response.user, chore)
            })

        chores_by_date.append({
            'date'    : date,
            'class'   : find_day_classes(date),
            'id'      : find_day_id(date),
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

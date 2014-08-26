from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import (login_required, user_passes_test,
    permission_required)
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.template import loader, Context
from django.utils import timezone

# Create your views here.

import datetime
import pytz
import itertools
import decimal

from utilities import timedelta
from utilities.views import DisplayInformation, format_balance
from chores.models import Chore
from profiles.models import UserProfile
from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange)

# TODO: put extra functions and lengthy variable definitions in another file.

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

def get_obligations(user, coop=None):

    if coop is None:
        coop = user.profile.coop

    upcoming_lower_boundary = datetime.date.today()
    upcoming_upper_boundary = (upcoming_lower_boundary+
            datetime.timedelta(days=coop.profile.release_buffer))
    all_chores = (Chore.objects.for_coop(coop).signed_up(user, True)
                     .order_by('start_date'))
    all_stewardships = Stewardship.objects.for_coop(coop).signed_up(
        user, True).order_by('start_date')
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
    data['ready for signature'] = (data['not signed off'].voided(None, False)
                               .filter(start_date__lte=datetime.date.today()))
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
    data.update(calculate_load_info(user=user, coop=coop)[0])

    def list_processor(items):
        return [
            {'items': item} for item in items if item
        ]

    def table_processor(items):

        def make_html_title(chores):
            return ', '.join(str(chore) for chore in chores)

        return [
            {'value': sum(chores),
             'html_title': make_html_title(chores)}
            for chores in items
        ]

    def summary_processor(items):
        def convert_to_integer(x):
        # TODO: this is wasteful when `value` is already an integer (which
        # has happened, at least with toy data).
        # TODO:  I think those 'integers' might be like 'Decimal('1')'. Check.
            return decimal.Decimal(x).to_integral_value()
        return [
            {'value': convert_to_integer(value),
             'html_title': 'Exact value: {val}'.format(val=value)}
            for value in items
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
            # TODO: should 'Needing Sign Off' be renamed 'Ready for Signature'?
                'subsections': [['Signed Up', 'Signed Off', 'Needing Sign Off',
                                 'Voided'],
                                ['Stewardships', 'Special Points', 'Loans']]
            }, [
                'all chores', 'signed off', 'ready for signature', 'voided',
                'stewardships', 'special points', 'loans'
            ], table_processor, 'per cycle'),
        DisplayInformation('summary_information', {
                'sections': ['Summary'],
                'subsections': [['New Due', 'New Credited',
                                 'Cumulative Balance']]
            }, [
                'load', 'credits', 'balance'
            ], summary_processor, None)
    ]
    dict_to_return = {
        display_info.name: display_info.create_template_data(data) for
        display_info in display_infos
    }
    dict_to_return['table_information'].insert(0,
        dict_to_return['summary_information'][0])
    dict_to_return.update({'point_cycles': cycles})
    return dict_to_return

# TODO: this method is quite long. See if there's a way to pull some of it out
# into another function.
def calculate_load_info(user=None, coop=None):
    if coop is None:
        if user is None:
            raise TypeError('Must specify user or co-op.')
        else:
            coop = user.profile.coop
    today = timezone.now().date()
    # Storing as a tuple so we can iterate over it multiple times without extra
    # cost. TODO: is this how this works?
    all_coopers = tuple(coop.user_set.all())
    if user is None:
        user_set = all_coopers
    else:
        user_set = (user,)
    # Note that we're not checking whether stewardships are voided or not
    # (since currently that doesn't happen/has no meaning/effect). Maybe
    # should be changed (TODO).
    data = {
        'chores'       : Chore.objects.for_coop(coop).voided(None, False),
        'stewardships' : Stewardship.objects.for_coop(coop),
        'absences'     : Absence.objects.for_coop(coop),
        'share changes': ShareChange.objects.for_coop(coop)
    }
    accounts = [{'user': cooper, 'load': [], 'credits': [], 'balance': []} for
                cooper in user_set]
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        cycle_data = {key: value.in_window(start_date, stop_date)
                      for key, value in data.items()}
        adds_to_points = tuple(itertools.chain(cycle_data['chores'],
                                               cycle_data['stewardships']))
        adds_to_presence = cycle_data['absences']
        adds_to_share = cycle_data['share changes']

        # TODO: could move around to iterate through only once.
        total_points   =  sum(adds_to_points)
        total_presence = -sum(adds_to_presence)+sum(cooper.profile.presence for
                                                    cooper in all_coopers)
        total_share    =  sum(adds_to_share)+sum(cooper.profile.share for
                                                 cooper in all_coopers)

        # 'ppds' stands for 'points per day-share.'
        # TODO: here and elsewhere, add error handling (for division).
        # base_presence = sum(cooper.profile.presence*cooper.profile.share for
                            # cooper in all_coopers)

        total_presence_share = 0
        presence_shares = {}
        for cooper in all_coopers:
            presence = cooper.profile.presence-sum(cycle_data['absences']
                                                   .signed_up(cooper, True))
            share = cooper.profile.share+sum(cycle_data['share changes']
                                             .signed_up(cooper, True))
            presence_share = presence*share
            total_presence_share += presence_share
            #TODO: don't like how this is done.
            if cooper in user_set:
                presence_shares.update({cooper: presence_share})
        ppds = total_points/total_presence_share

        for dict_ in accounts:
            user = dict_['user']
            #TODO: for now I like it as it is, but you could consider having
            #loans directly affect the load.
            load = ppds*presence_shares[user]
            #Handling chores and stewardships separately to avoid any confusion
            #about how stewardships are handled.
            user_signed_up_chores = cycle_data['chores'].signed_up(user, True)
            total_signed_up = sum(user_signed_up_chores)
            total_completed = sum(user_signed_up_chores.signed_off(None, True))
            credits = (total_signed_up if today <= stop_date else
                total_completed)
            credits += sum(cycle_data['stewardships'].signed_up(user, True))
            try:
                old_balance = dict_['balance'][-1]
            except IndexError:
                old_balance = 0
            balance = credits-load+old_balance
            dict_['load'].append(load)
            dict_['credits'].append(credits)
            dict_['balance'].append(balance)
    return accounts

def calculate_balance(user, coop=None):
    load_info = calculate_load_info(user=user, coop=coop)[0]
    return format_balance(load=load_info['load'][-1],
                                    balance=load_info['balance'][-1])

@ensure_csrf_cookie
@login_required()
def chores_list(request):

    # TODO: Would be nice to able for selecting by 'today' as well as by date.
    def find_day_id(date):
        return date.isoformat()

    def find_day_name(date):
        #TODO: use timezones for this.
        difference = (date-timezone.now().date()).days
        translations = {-1: 'yesterday', 0: 'today', 1: 'tomorrow'}
        return translations.get(difference, '')

    def find_day_classes(date):
        '''
        Sets flags relating to `date` that are read by the template. The actual
        formatting information is kept in a CSS file.
        '''
        now = datetime.date.today()
        difference = date-now
        css_classes = {
            'day_near_past'  : timedelta.in_interval(None, difference, -3),
            'day_current'    : timedelta.in_interval(  -3, difference,  0),
            'day_near_future': timedelta.in_interval(   0, difference,  3),
        }
        return ' '.join([key for key,value in css_classes.items() if value])

    def find_cycle_classes(cycle_num, start_date, stop_date):
        '''
        Sets flags relating to `cycle` that are read by the template. The
        actual formatting information is kept in a CSS file.
        '''
        today = datetime.date.today()
        css_classes = {
            'cycle_past'   : today < start_date,
            'cycle_current': start_date <= today <= stop_date,
            'cycle_future' : stop_date < today,
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
    coop = request.user.profile.coop
    chores = Chore.objects.for_coop(coop)
    cycles = []
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        chores_by_date = []
        for date in timedelta.daterange(start_date, stop_date, inclusive=True):
            chores_today = (chores.filter(start_date=date)
                              .order_by('skeleton__start_time',
                                        'skeleton__short_name'))
            if chores_today:
                chore_dicts = [{
                        'chore': chore,
                        'class': chore.find_CSS_classes(request.user),
                        'sentences': get_chore_sentences(request.user, chore)
                } for chore in chores_today]
                chores_by_date.append({
                    'date'    : date,
                    'class'   : find_day_classes(date),
                    'id'      : find_day_id(date),
                    'name'    : find_day_name(date),
                    'schedule': chore_dicts,
                    'weekday' : weekdays[date.weekday()],
                 })
        cycles.append({
            'days': chores_by_date,
            'class': find_cycle_classes(cycle_num, start_date, stop_date),
            'id': cycle_num,
        })
    return render(request,'chores/chores_list.html', dictionary={
        'coop': coop, 'cycles': cycles,
        'current_balance': calculate_balance(request.user, coop)
    })

# TODO: write a function/URL thing for when they go to 'chores/me/'.
# TODO: this should now require permissions.
@login_required()
def user_stats_list(request, username):
    #For the scenario that an anonymous user clicks the 'stats' link, logs in,
    #and is then sent to chores/AnonymousUser/'.
    if username == 'AnonymousUser':
        return redirect('/chores/{usn}/'.format(usn=request.user))
    user = User.objects.get(username=username)
    coop = user.profile.coop
    render_dictionary = {
        'coop': coop,
        'cooper': user,
    }
    render_dictionary.update(get_obligations(user, coop=coop))
    return render(request, 'chores/user_stats_list.html',
                  dictionary=render_dictionary)

# TODO: allow for people to download it either way if they're logged in?
def calendar_create(request, username):
    # Test to see if that user wants a public calendar. Also do error checking
    # with this next step.
    user = User.objects.get(username=username)
    if not user.profile.public_calendar:
        return HttpResponse('User has not enabled a public calendar.',
                            status=403)
    coop = user.profile.coop
    # TODO: could remove voided chores.
    chores = Chore.objects.for_coop(coop).signed_up(user, True)
    response = HttpResponse(content_type='text/calendar')
    response['Content-Disposition'] = ('attachment; '
        'filename="{sho}_chore_calendar.ics"'.format(
            sho=coop.profile.short_name.replace(' ', '_')))
    template = loader.get_template('calendars/calendar.ics')
    context = Context({'coop': coop, 'chores': chores})
    response.write(template.render(context))
    return response


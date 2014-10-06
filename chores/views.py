from django.db import connection, reset_queries

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import (login_required, user_passes_test,
    permission_required)
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
from django.template import loader, Context
from django.utils import timezone

import datetime
import pytz
import itertools
import decimal
import math
import collections

from utilities import timedelta
from utilities.views import DisplayInformation, format_balance
from chores.models import Chore, ChoreSkeleton
from profiles.models import UserProfile
from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange)

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

    def __init__(self, user, chore, chore_attribute=None):
        if chore_attribute is not None:
            self.chore_attribute = chore_attribute
        #TODO: should this use the co-op's timezone? Look to see how chore dates
        #are stored. Check here and everywhere else.
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
        # TODO: could make new QuerySets/models/whatever in for these.
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
    today = coop.profile.today()
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

    def find_day_id(date):
        return date.isoformat()

    def find_day_name(date, coop):
        today = coop.profile.today()
        translations = {-1: 'yesterday', 0: 'today', 1: 'tomorrow'}
        return translations.get((date-today).days, '')

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
    # Here (and elsewhere) we assume that a User is a member of only one Group.
    coop = request.user.profile.coop
    #print('before getting chore skeletons: {lcn}'.format(
        #lcn=len(connection.queries)))
    chore_skeletons = set(ChoreSkeleton.objects.for_coop(coop=coop))
    #print('after getting chore skeletons: {lcn}'.format(
        #lcn=len(connection.queries)))
    chores = Chore.objects.filter(skeleton__in=chore_skeletons)
    cycles = []
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        chores_this_cycle = (chores.filter(start_date__gte=start_date,
                                           start_date__lte=stop_date)
            .prefetch_related('signed_up__who__profile',
                'signed_off__who__profile', 'voided__who__profile', 'skeleton')
        )
        sorted_chores = collections.defaultdict(list)
        for chore in chores_this_cycle:
            sorted_chores[chore.start_date].append(chore)

        chores_by_date = []
        #print('checking at beginning of cycle {cyn}: {lcn}'.format(
            #cyn=cycle_num, lcn=len(connection.queries)))
        for date in timedelta.daterange(start_date, stop_date, inclusive=True):
            chores_today = sorted_chores[date]
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
                    'name'    : find_day_name(date, coop),
                    'schedule': chore_dicts,
                    'weekday' : weekdays[date.weekday()],
                 })
            #print('checking at end of {dat}: {lcn}'.format(dat=date,
                #lcn=len(connection.queries)))
        cycles.append({
            'days': chores_by_date,
            'class': find_cycle_classes(cycle_num, start_date, stop_date),
            'id': cycle_num,
        })
    return render(request,'chores/chores_list.html', dictionary={'coop': coop,
        'cycles': cycles})

@login_required()
def user_stats_list(request, username):
    #For the scenario that an anonymous user clicks the 'stats' link, logs in,
    #and is then sent to chores/AnonymousUser/'.
    #TODO: use `User.is_authenticated` or something instead?
    if username == 'AnonymousUser':
        return redirect('/chores/{usn}/'.format(usn=request.user))
    #TODO: before doing this, we should make 'me' a prohibited username.
    #elif username == 'me':
        #user = request.user
    else:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponse('No such user.', status=404)
    #TODO: check that `request.user` is the points steward for the co-op `user`
    #is a member of.
    if (request.user != user and not request.user.profile.points_steward):
        return HttpResponse(
            'You are neither {nic} nor the Points Steward.'.format(
                nic=user.profile.nickname),
            status=403
        )
    coop = user.profile.coop
    render_dictionary = {
        'coop': coop,
        'cooper': user,
    }
    render_dictionary.update(get_obligations(user, coop=coop))
    return render(request, 'chores/user_stats_list.html',
                  dictionary=render_dictionary)

def calendar_create(request, username):
    #TODO: this code is repeated. Could make a function.
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
            return HttpResponse('No such user.', status=404)
    if not user.profile.public_calendar and request.user != user:
        return HttpResponse('User has not enabled a public calendar.',
                            status=403)
    coop = user.profile.coop
    chores = Chore.objects.for_coop(coop).signed_up(user, True)
    response = HttpResponse(content_type='text/calendar')
    response['Content-Disposition'] = ('attachment; '
        'filename="{sho}_chore_calendar.ics"'.format(
            sho=coop.profile.short_name.replace(' ', '_')))
    template = loader.get_template('calendars/calendar.ics')
    context = Context({'coop': coop, 'chores': chores})
    response.write(template.render(context))
    return response

@login_required()
def balances_summarize(request, num_columns=5):
    coop = request.user.profile.coop
    accounts = calculate_load_info(coop=coop)
    accounts.sort(key=lambda x: x['user'].profile.nickname)
    accounts = [{
        'cooper': row['user'],
        'balance': format_balance(load=row['load'][-1],
                                  balance=row['balance'][-1])
    } for row in accounts]
    #TODO: find a better way to do this. Could use itertools, maybe. Keep in
    #mind template limitations.
    num_rows = math.ceil(len(accounts)/num_columns)
    #Fill out the shorter columns.
    while len(accounts) % num_rows:
        accounts.append(None)
    accounts = [list(accounts[i*num_columns+j] for j in range(num_columns))
                for i in range(num_rows)]
    return render(request, 'chores/balances_summarize.html',
                  {'accounts': accounts})


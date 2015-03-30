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
from utilities.views import TableElement, TableParent, format_balance
from chores.models import Chore, ChoreSkeleton
from profiles.models import UserProfile
from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange)

def pretty_print_query(query):
    import string
    query = str(query).replace(', ', ',\n')
    print(query)

class ChoreSentence():
    chore_attribute = None
    past_participle = None
    action_permission_attribute = None
    reversion_permission_attribute = None

    def __init__(self, user, chore, chore_attribute=None):
        if chore_attribute is not None:
            self.chore_attribute = chore_attribute
        #TODO: should this use the co-op's timezone? Look to see how chore
        #dates are stored. Check here and everywhere else.
        # Otherwise use the class attribute.
        self.user = user
        self.chore = chore
        self.signature = getattr(self.chore, self.chore_attribute)
        self.owner = self.signature.who

    def action_permitted(self):
        return any(
            getattr(self.chore, attribute)(self.user)['boolean']
            for attribute in (self.action_permission_attribute,
                              self.reversion_permission_attribute)
        )

    def text(self):
        return '{nam} {ppa}.'.format(
            nam='You' if self.owner == self.user else
                self.owner.profile.nickname,
            ppa=self.past_participle
        ) if self.signature else None

class VoidSentence(ChoreSentence):
    chore_attribute = 'voided'
    past_participle = 'voided'
    action_permission_attribute = 'void_permission'
    reversion_permission_attribute = 'revert_void_permission'

class SignUpSentence(ChoreSentence):
    chore_attribute = 'signed_up'
    past_participle = 'signed up'
    action_permission_attribute = 'sign_up_permission'
    reversion_permission_attribute = 'revert_sign_up_permission'

class SignOffSentence(ChoreSentence):
    chore_attribute = 'signed_off'
    past_participle = 'signed off'
    action_permission_attribute = 'sign_off_permission'
    reversion_permission_attribute = 'revert_sign_off_permission'

def get_chore_button(user, chore):
    sentences = [
        constructor(user, chore)
        for constructor in (SignUpSentence, SignOffSentence, VoidSentence)
    ]
    texts = [sentence.text() for sentence in sentences]
    permissions = [sentence.action_permitted() for sentence in sentences]
    return {
        'text': ' '.join(filter(None, texts)),
        #Separate the voiding permissions.
        'enabled': any(permissions[0:2]),
        'void_enabled': permissions[2],
    }

def get_obligations(user, coop=None):
    if coop is None:
        coop = user.profile.coop
    upcoming_lower_boundary = datetime.date.today()
    upcoming_upper_boundary = (upcoming_lower_boundary+
            datetime.timedelta(days=coop.profile.release_buffer))
    all_chores = Chore.objects.for_coop(coop).signed_up(user, True).order_by(
        'start_date').prefetch_related('skeleton', 'signed_up', 'signed_off',
                                       'voided')
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
        'stewardships': all_stewardships.classical(),
        'special points': all_stewardships.special_points(),
        'loans': all_stewardships.loan(),
        'absences': Absence.objects.signed_up(user, True),
        'share changes': ShareChange.objects.signed_up(user, True)
    }
    #TODO: use `coop.profile` timezone thing.
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
    data.update(calculate_load_info(user=user, coop=coop)[0])

    list_sections = [
        TableParent(title=section[0], children=[
            TableParent(title=title, children=[
                TableElement(content=str(chore))
                for chore in data[key]['original']
            ]) for title, key in zip(section[1], section[2])
        ]) for section in (
            ('Chores',
             ('Upcoming', 'Voided', 'Ready for Signature',),
             ('upcoming chores', 'voided', 'ready for signature',),),
            ('Stewardships and Similar',
             ('Stewardships', 'Special Points', 'Loans',),
             ('stewardships', 'special points', 'loans',),),
            ('Benefit Changes',
             ('Absences', 'Share Changes',),
             ('absences', 'share changes',),),
        )
    ]
    for section in list_sections:
        section.children = list(filter(lambda subsection: any(
            element.content for element in subsection.children),
            section.children))
    list_sections = list(filter(lambda section: any(subsection.children for
        subsection in section.children), list_sections))
    table_summary_sections = [
        TableParent(title=section[0], children=[
            TableParent(title=title, children=[
                TableElement(title='Exact value: {val}'.format(val=value),
                    content=decimal.Decimal(value).to_integral_value())
                for value in data[key]
            ]) for title, key in zip(section[1], section[2])
        ]) for section in (
            ('Summary',
             ('New Due', 'New Credited', 'Cumulative Balance',),
             ('load', 'credits', 'balance',),),
        )
    ]

    keys = ('all chores', 'signed off', 'ready for signature', 'voided')
    table_specific_sections = [
        TableParent(title=section[0], children=[
            TableParent(title=title, children=[
                TableElement(content=sum(chores), title=', '.join(
                    str(chore) for chore in chores))
                for chores in data[key]['per cycle']
            ]) for title, key in zip(section[1], section[2])
        ]) for section in (
            ('Chores',
             ('Signed Up', 'Signed Off', 'Needing Sign Off', 'Voided',),
             ('all chores', 'signed off', 'ready for signature', 'voided',),),
            ('Stewardships and Similar',
             ('Stewardships', 'Special Points', 'Loans',),
             ('stewardships', 'special points', 'loans',),),
        )
    ]
    return {'point_cycles': cycles, 'table_sections': table_summary_sections+
            table_specific_sections, 'list_sections': list_sections}

# TODO: this method is quite long. See if there's a way to pull some of it out
# into another function.
def calculate_load_info(user=None, coop=None):

    def absence_summer(absences, cycle_start_date, cycle_stop_date):
        total = 0
        for absence in absences:
            #Add 1 to count both endpoints.
            total += (min(absence.stop_date,  cycle_stop_date)-
                      max(absence.start_date, cycle_start_date)).days+1
        return total

    if coop is None:
        if user is None:
            raise TypeError('Must specify user or co-op.')
        else:
            coop = user.profile.coop
    today = coop.profile.today()
    # Storing as a tuple so we can iterate over it multiple times without extra
    # cost. TODO: is this how this works?
    all_coopers = tuple(coop.user_set.all().prefetch_related('profile'))
    if user is None:
        user_set = all_coopers
    else:
        user_set = (user,)
    # Note that we're not checking whether stewardships are voided or not
    # (since currently that doesn't happen/has no meaning/effect). Maybe
    # should be changed (TODO).
    data = {
        #TODO: lots of quick fixes here. Needs more thought and efficiency.
        'chores'       : Chore.objects.for_coop(coop).voided(None, False),
        'stewardships' : Stewardship.objects.for_coop(coop),
        'absences'     : Absence.objects.for_coop(coop),
        'share changes': ShareChange.objects.for_coop(coop),
    }
    #TODO: only necessary to get accounts for coopers in `user_set`.
    accounts = {cooper: {'user': cooper, 'load': [], 'credits': [],
                         'balance': []} for cooper in all_coopers}
    olcn = len(connection.queries)
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        olcn = len(connection.queries)
        cycle_data = {key: value.in_window(start_date, stop_date)
                      for key, value in data.items()}
        cycle_data['chores'] = cycle_data['chores'].prefetch_related(
            'signed_up__who', 'signed_off__who', 'skeleton')
        for key in ('stewardships', 'absences', 'share changes'):
            cycle_data[key] = cycle_data[key].prefetch_related(
                'signed_up__who', 'skeleton')
        olcn = len(connection.queries)
        adds_to_points = itertools.chain(cycle_data['chores'],
                                         cycle_data['stewardships'])
        total_points = sum(adds_to_points)
        #TODO:  Doesn't increase (or decrease) database hits. However, if you
        #decide to totally strip out `__radd__` usage, can use this. I think
        #that might be a good thing to do.
        #total_points = 0
        #for chore in cycle_data['chores']:
            #total_points += chore.skeleton.point_value
        #for stewardship in cycle_data['stewardships']:
            #total_points += stewardship.skeleton.point_value
        olcn = len(connection.queries)
        presences = {cooper: cooper.profile.presence for cooper in all_coopers}
        shares = {cooper: cooper.profile.share for cooper in all_coopers}
        #TODO: this assumes that all absences are signed up for.
        for absence in cycle_data['absences']:
            presences[absence.signed_up.who] -= absence.window_overlap(
                start_date, stop_date)
        for share_change in cycle_data['share changes']:
            shares[share_change.signed_up.who] += share_change.share_change
        total_presence_share = sum(presence*share for presence, share in
                                   zip(presences.values(), shares.values()))
        presence_shares = {cooper: presences[cooper]*shares[cooper]
                           for cooper in all_coopers}
        total_presence_share = sum(presence_shares.values())
        # 'ppds' stands for 'points per day-share.'
        ppds = total_points/total_presence_share

        #Initialize credit count for this cycle.
        for account in accounts.values():
            account['credits'].append(0)
        olcn = len(connection.queries)
        if today <= stop_date:
            for chore in cycle_data['chores']:
                if chore.signed_up:
                    accounts[chore.signed_up.who]['credits'][-1] += (
                        chore.skeleton.point_value)
        else:
            for chore in cycle_data['chores']:
                #Superfluous to check that the chore is signed up. Better to
                #check again or trust controls on signing off?
                if chore.signed_up and chore.signed_off:
                    accounts[chore.signed_up.who]['credits'][-1] += (
                        chore.skeleton.point_value)
        for stewardship in cycle_data['stewardships']:
            accounts[stewardship.signed_up.who]['credits'][-1] += (
                stewardship.skeleton.point_value)
        for cooper, account in accounts.items():
            load = ppds*presence_shares[cooper]
            try:
                old_balance = account['balance'][-1]
            except IndexError:
                old_balance = 0
            balance = account['credits'][-1]-load+old_balance
            account['load'].append(load)
            account['balance'].append(balance)
    return [account for cooper, account in  accounts.items()
            if cooper in user_set]

def calculate_balance(user, coop=None):
    load_info = calculate_load_info(user=user, coop=coop)[0]
    return format_balance(load=load_info['load'][-1],
                          balance=load_info['balance'][-1])

@login_required()
def user_stats_list(request, username):
    reset_queries()
    #For the scenario that an anonymous user clicks the 'stats' link, logs in,
    #and is then sent to chores/AnonymousUser/'.
    #TODO: use `User.is_authenticated` or something instead?
    if username == 'AnonymousUser':
        return redirect('/chores/{usn}/'.format(usn=request.user))
    else:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponse('No such user.', status=404)
    #TODO: check that `request.user` is the points steward for the co-op `user`
    #is a member of.
    coop = user.profile.coop
    #The requesting user can see the stats for themself and, if they are the
    #points steward, the other users of their coop.
    #TODO: maybe could shave off a database hit by comparing `coop.id` and
    #`request.user.profile.coop.id` instead of fetching entire object.
    if (request.user != user and not (request.user.profile.points_steward and
                                      request.user.profile.coop == coop)):
        return HttpResponse(
            'You are neither {nic} nor the Points Steward.'.format(
                nic=user.profile.nickname),
            status=403
        )
    render_dictionary = {
        'coop': coop,
        'cooper': user,
    }
    render_dictionary.update(get_obligations(user, coop=coop))
    return render(request, 'chores/user_stats_list.html',
                  dictionary=render_dictionary)

@login_required()
def chores_list(request):
    return render(request, 'chores/chores_list.html')

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
    chores = (Chore.objects.for_coop(coop).signed_up(user, True)
        .prefetch_related('skeleton', 'signed_up'))
    response = HttpResponse(content_type='text/calendar')
    response['Content-Disposition'] = ('attachment; '
        'filename="{sho}_chore_calendar.ics"'.format(
            sho=coop.profile.short_name.replace(' ', '_')))
    template = loader.get_template('calendars/calendar.ics')
    context = Context({'coop': coop, 'chores': chores})
    response.write(template.render(context))
    return response

@login_required()
def balances_summarize(request, num_columns=1):
    coop = request.user.profile.coop
    accounts = calculate_load_info(coop=coop)
    accounts.sort(key=lambda x: x['user'].profile.nickname)
    #TODO: here and elsewhere, call some sort of function to get active users.
    accounts = [{
        'cooper': row['user'],
        'balance': format_balance(load=row['load'][-1],
                                  balance=row['balance'][-1])
    } for row in accounts if row['user'].is_active]
    max_width = max(len(account['balance']['formatted_value'])
                    for account in accounts)
    for account in accounts:
        current = account['balance']['formatted_value']
        account['balance']['formatted_value'] = '{sgn}{pad}{val}'.format(
            sgn=current[0], pad='0'*(max_width-len(current)), val=current[1:])
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


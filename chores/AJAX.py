from django.db import connection, reset_queries

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.decorators import (login_required, user_passes_test,
    permission_required)
from django.views.decorators.csrf import ensure_csrf_cookie

import collections
import datetime
import json
from chores.models import Chore, ChoreSkeleton, ChoreError
from chores.forms import ChoreSkeletonForm, ChoreFormCreator
from chores.views import get_chore_sentences, calculate_balance
from utilities import timedelta
from utilities.AJAX import (make_form_response, create_function_creator,
    edit_function_creator)

@login_required()
def updates_fetch(request):
    print('in AJAX.updates_fetch')
    try:
        milliseconds = int(request.GET.get('milliseconds', ''))
    except ValueError as e:
        #TODO: return an error.
        milliseconds = 10

    if not milliseconds:
        return HttpResponse('', reason='No milliseconds value provided.',
                            status=400)
    print('milliseconds: {ms}'.format(ms=milliseconds))
    cutoff = datetime.datetime.utcfromtimestamp(milliseconds/1000).replace(
        tzinfo=timezone.get_default_timezone())
    changed_chores = Chore.objects.for_coop(request.user.profile.coop).filter(
        updated__gte=cutoff).prefetch_related('signed_up__who__profile',
        'signed_off__who__profile', 'voided__who__profile')
    print('about to call updates_report')
    return updates_report(request, chores=changed_chores,
                          include_balances=True)

@ensure_csrf_cookie
@login_required()
def chores_fetch(request):
    reset_queries()

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
        #TODO: think I applied a fix here. Check that it's working.
        css_classes = {
            'cycle_past'   : stop_date < today,
            'cycle_current': start_date <= today <= stop_date,
            'cycle_future' : today < start_date,
        }
        return ' '.join([key for key,value in css_classes.items() if value])

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                'Saturday', 'Sunday']
    # Here (and elsewhere) we assume that a User is a member of only one Group.
    coop = request.user.profile.coop

    try:
        cycle_offset = int(request.GET.get('cycle_offset', 0))
    except ValueError as e:
        #TODO: here `status` should be pulled from `e` (?).
        return HttpResponse('', reason=e, status=400)
    chores = Chore.objects.for_coop(coop)
    cycles = []
    for cycle_num, start_date, stop_date in coop.profile.cycles(
        offset=cycle_offset):
        #TODO: look into fetching all chores and then sorting in Python.
        chores_this_cycle = (chores.filter(start_date__gte=start_date,
                                           start_date__lte=stop_date)
            .prefetch_related('skeleton', 'signed_up__who__profile',
                'signed_off__who__profile', 'voided__who__profile')
            .order_by('-skeleton__sort_index', 'skeleton__start_time',
                      'skeleton__short_name')
        )
        sorted_chores = collections.defaultdict(list)
        for chore in chores_this_cycle:
            sorted_chores[chore.start_date].append(chore)

        chores_by_date = []
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
        if chores_by_date:
            #TODO: might want to change these keys.
            cycles.append({
                'days': chores_by_date,
                'class': find_cycle_classes(cycle_num, start_date, stop_date),
                'id': cycle_num,
            })
    if cycles:
        return HttpResponse(json.dumps({
            'html': render_to_string('chores/chores_list_cycle.html',
                                     {'coop': coop, 'cycles': cycles}),
            'least_cycle_num': min(int(cycle['id']) for cycle in cycles),
        }), status=200)
    else:
        return HttpResponse('', reason='No chores found.', status=204)

def updates_report(request, chores=None, include_balances=False,
                   balance_change=None):
    chores = {chore.id: {
        'sentences': [sentence.dict_for_json() for sentence in
                      get_chore_sentences(request.user, chore)],
        'CSS_classes': chore.find_CSS_classes(request.user),
    } for chore in chores}
    request_dict = {'chores': chores}
    if include_balances:
        request_dict.update({
            'current_balance': calculate_balance(request.user)
        })
    if balance_change is not None:
        request_dict.update({'balance_change': balance_change})
    return HttpResponse(json.dumps(request_dict), status=200)

#TODO: also take `method_name` from `request.POST`? Would be a little involved,
#since there's creating/editing/fetching as well, and they use different
#request methods.
@login_required()
def act(request, method_name):
    user = request.user
    try:
        chore_id = int(request.POST.get('chore_id', ''))
    except ValueError as e:
        #TODO: here `status` should be pulled from `e` (?).
        return HttpResponse('', reason=e, status=400)
    if not chore_id:
        return HttpResponse('', reason='No chore ID provided.', status=400)
    whitelist = ('sign_up', 'sign_off', 'void', 'revert_sign_up',
                 'revert_sign_off', 'revert_void')
    if method_name not in whitelist:
        return HttpResponse('', reason='Method name not permitted.',
                            status=403)
    #TODO: either use `Chore.DoesNotExist` here or use `ObjectDoesNotExist`
    #everywhere.
    try:
        chore = Chore.objects.get(pk=chore_id)
    except ObjectDoesNotExist as e:
        return HttpResponse('', reason=e.args[0], status=404)
    try:
        getattr(chore, method_name)(user)
    except ChoreError as e:
        #TODO: here `status` should be pulled from `e`.
        return HttpResponse('', reason=e, status=403)

    #TODO: change to method that gets current cycle if you make one.
    coop = user.profile.coop
    for cycle_num, start_date, stop_date in coop.profile.cycles():
        pass
    current_cycle = chore.start_date >= start_date
    my_chore = chore.signed_up.who == user
    point_value = chore.skeleton.point_value
    balance_change = {
        'sign_up': point_value if current_cycle else 0,
        'sign_off': 0,
        'void': -point_value if current_cycle and my_chore else 0,
        'revert_sign_up': -point_value if current_cycle else 0,
        'revert_sign_off': 0,
        'revert_void': point_value if current_cycle and my_chore else 0,
    }[method_name]
    return updates_report(request, chores=(chore,), include_balances=False,
                          balance_change=balance_change)

chore_skeleton_create = create_function_creator(model=ChoreSkeleton,
                                                model_form=ChoreSkeletonForm)
chore_skeleton_edit = edit_function_creator(model=ChoreSkeleton,
                                            model_form=ChoreSkeletonForm)
chore_create = create_function_creator(model=Chore,
                                       model_form_callable=ChoreFormCreator)
chore_edit = edit_function_creator(model=Chore,
                                   model_form_callable=ChoreFormCreator)

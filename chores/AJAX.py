from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

import datetime
import json
from chores.models import Chore, ChoreSkeleton, ChoreError
from chores.forms import ChoreSkeletonForm, ChoreFormCreator
from chores.views import get_chore_sentences, calculate_balance
from utilities.AJAX import (make_form_response, create_function_creator,
    edit_function_creator)

@login_required()
def updates_fetch(request):
    milliseconds = int(request.GET.get('milliseconds', ''))
    if not milliseconds:
        return HttpResponse('', reason='No milliseconds value provided.',
                            status=400)
    cutoff = datetime.datetime.utcfromtimestamp(milliseconds/1000).replace(
        tzinfo=timezone.get_default_timezone())
    changed_chores = Chore.objects.for_coop(request.user.profile.coop).filter(
        updated__gte=cutoff).prefetch_related('signed_up__who__profile',
        'signed_off__who__profile', 'voided__who__profile')
    return updates_report(request, chores=changed_chores,
                          include_balances=True)

def updates_report(response, chores=None, include_balances=False,
                   balance_change=None):
    chores = {chore.id: {
        'sentences': [sentence.dict_for_json() for sentence in
                      get_chore_sentences(response.user, chore)],
        'CSS_classes': chore.find_CSS_classes(response.user),
    } for chore in chores}
    response_dict = {'chores': chores}
    if include_balances:
        response_dict.update({
            'current_balance': calculate_balance(response.user)
        })
    if balance_change is not None:
        response_dict.update({'balance_change': balance_change})
    return HttpResponse(json.dumps(response_dict), status=200)

#TODO: also take `method_name` from `request.POST`? Would be a little involved,
#since there's creating/editing/fetching as well, and they use different
#request methods.
@login_required()
def act(request, method_name):
    user = request.user
    chore_id = int(request.POST.get('chore_id', ''))
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

#TODO: move this into the bulk creation.
@login_required()
def chore_create_TO_CHANGE(request):
    raise NotImplementedError
    form = ChoreForm(request.POST)
    if form.is_valid():
        #Django (as of version 1.6.5) doesn't permit bulk creation of
        #inherited models, and Chore inherits from Timecard. So we have to do
        #it one-by-one. Haven't managed to get it working with Signatures,
        #either. Guessing a problem with pk? See <https://docs.djangoproject
        #.com/en/dev/ref/models/querysets/#bulk-create>.
        repeat_interval = datetime.timedelta(days=form.cleaned_data[
            'repeat_interval'])
        for repeat in range(form.cleaned_data['number_of_repeats']):
            shift = repeat*repeat_interval
            chore = Chore.objects.create_blank(
                skeleton=form.cleaned_data['skeleton'],
                start_date=form.cleaned_data['start_date']+shift,
                stop_date=form.cleaned_data['stop_date']+shift,
            )
    return make_form_response(form)

def chore_edit_TO_CHANGE(request):
    raise NotImplementedError

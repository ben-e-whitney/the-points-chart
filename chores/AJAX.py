from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import json
from profiles.AJAX import make_form_response
from chores.models import Chore, ChoreError, Signature
from chores.forms import ChoreSkeletonForm, ChoreForm
from chores.views import get_chore_sentences, calculate_balance


# TODO: still not used here!
def add_current_balance(f):

    def inner(*args, **kwargs):
        request = args[0]
        response = f(*args, **kwargs)
        # response['current_balance'] = calculate_balance(request.user)
        # TODO: only do this when the status is 200 (success) or similar? Might
        # have to make a check in the JavaScript function, which would be fine.
        response['current_balance'] = calculate_balance(request.user)
        return response

    return inner

def action_response(user, chore):
    sentences = get_chore_sentences(user, chore)
    # TODO: get rid of this? Skimming now seems to do nothing.
    for sentence in sentences:
        json.dumps({'sentence': sentence.dict_for_json()})
    json.dumps({'CSS_classes': chore.find_CSS_classes(user)})
    return HttpResponse(json.dumps({
        'sentences': [sentence.dict_for_json() for sentence in
                      get_chore_sentences(user, chore)],
        'CSS_classes': chore.find_CSS_classes(user),
        'current_balance': calculate_balance(user)
    }), status=200)

@login_required()
def act(response, method_name, chore_id):
    whitelist = ('sign_up', 'sign_off', 'void', 'revert_sign_up',
                 'revert_sign_off', 'revert_void')
    if method_name not in whitelist:
        return HttpResponse('', reason='Method name not permitted.',
                            status=403)
    try:
        chore = Chore.objects.get(pk=chore_id)
    except ObjectDoesNotExist as e:
        return HttpResponse('', reason=e.args[0], status=404)
    try:
        getattr(chore, method_name)(response.user)
    except ChoreError as e:
        return HttpResponse('', reason=e.args[0]['message'],
                            status=e.args[0]['status'])
    return action_response(response.user, chore)

# TODO: another permissions test here, and for the rest.
@login_required()
def chore_skeleton_create(request):
    form = ChoreSkeletonForm(request.POST)
    if form.is_valid():
        skeleton = form.save(commit=False)
        skeleton.coop = request.user.profile.coop
        skeleton.save()
    return make_form_response(form)

@login_required()
def chore_create(request):
    print('got to here')
    form = ChoreForm(request.POST)
    print('about to check whether form is valid')
    try:
        form.is_valid()
    except Exception as e:
        print(e)
        raise e
    if form.is_valid():
        print('form is valid')
        try:
            chore = form.save(commit=False)
            for signature in ('signed_up', 'signed_off', 'voided'):
                sig = Signature()
                sig.save()
                setattr(chore, signature, sig)
            chore.save()
        except Exception as e:
            print(e)
            raise e
    else:
        print('form is not valid')
    return make_form_response(form)

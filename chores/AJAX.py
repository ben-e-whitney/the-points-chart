from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json
import pytz
import datetime
from chores.models import Chore
from chores.views import get_chore_sentences

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
def action_response(user, chore):
    sentences = get_chore_sentences(user, chore)
    for sentence in sentences:
        json.dumps({'sentence': sentence.dict_for_json()})
    json.dumps({'css_classes': chore.find_CSS_classes(user)})

    return HttpResponse(json.dumps({
        'sentences': [sentence.dict_for_json() for sentence in
                      get_chore_sentences(user, chore)],
        'css_classes': chore.find_CSS_classes(user)
    }), status=200)

@login_required()
def sign_up(response, chore_id):
    chore = Chore.objects.get(pk=chore_id)
    if not chore.sign_up_permitted():
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        # TODO: after making timezone stuff work here make those changes
        # everywhere else.
        # TODO: could make special case if `response.user` was the one who
        # voided or signed up.
        if chore.voided:
            reason = '{coo} voided this chore '.format(
                coo=chore.voided.who.profile.nickname)
        else:
            # Someone else has signed up.
            reason = '{coo} signed up for this chore '.format(
                coo=chore.signed_up.who.profile.nickname)

        return HttpResponse('', reason=reason+'{tdp}'.format(
            tdp=timedelta_pretty_print(datetime.datetime.now(pytz.utc)-\
                chore.signed_up.when)), status=403)
    else:
        chore.signed_up.sign(response.user)
        # TODO: some repetition here with the chores templates. How to fix?
        # TODO: only use "Sign-off needed!" if we're in the past?
        return action_response(response.user, chore)

@login_required()
def sign_off(response, chore_id):
    chore = Chore.objects.get(pk=chore_id)
    if not chore.sign_off_permitted():
        # Error: no one has signed up. User should only be able to get here my
        # manually entering a URL.
        # TODO: add in more specific error messages here.
        return HttpResponse('', reason='This chore is not eligible for being '
                            'signed off.', status=403)
    # if chore.signed_off:
        # # Error: someone has already signed up. Return who has signed up and
        # # when they signed up. Return an error code so the JavaScript function
        # # can display this in an alert.
        # return HttpResponse('', reason='{coo} signed off on this chore {tdp}.'\
            # .format(coo=chore.signed_off.who.profile.nickname, tpd=\
                # timedelta_pretty_print(datetime.datetime.now()-\
                    # chore.when_signed_off)), status=403)
    elif response.user == chore.signed_up.who:
        # Error: can't sign off on your own chore. Have this pop up in an
        # alert.
        return HttpResponse('', reason="You can't sign off on your own "
                            "chore.", status=403)
    else:
        chore.signed_off.sign(response.user)
        return action_response(response.user, chore)

@login_required()
def void(response, chore_id):
    chore = Chore.objects.get(pk=chore_id)
    if not chore.void_permitted():
        return HttpResponse('', reason='This chore is not eligible for being '
                            'voided.', status=403)
    else:
        # TODO: abstract one more level, even, with chore.void(user) thing?
        # Could even return error codes!
        chore.voided.sign(response.user)
        return action_response(response.user, chore)

# TODO: standardize all these. Might be OK to just have 'operation not
# permitted' if the only way the function will be accessed is by someone
# messing around.
@login_required()
def revert_sign_up(response, chore_id):
    chore = Chore.objects.get(pk=chore_id)
    if not chore.revert_sign_up_permitted():
        return HttpResponse('', reason='Operation not permitted.', status=403)
    elif chore.signed_up.who != response.user:
        return HttpResponse('', reason="You didn't sign up for this chore!",
                            status=403)
    else:
        chore.signed_up.clear()
        return action_response(response.user, chore)

@login_required()
def revert_sign_off(response, chore_id):
    chore = Chore.objects.get(pk=chore_id)
    if not chore.revert_sign_off_permitted():
        return HttpResponse('', reason='Operation not permitted.', status=403)
    elif chore.signed_off.who != response.user:
        return HttpResponse('', reason="You didn't sign off on this chore!",
                            status=403)
    else:
        chore.signed_off.clear()
        return action_response(response.user, chore)

@login_required()
def revert_void(response, chore_id):
    chore = Chore.objects.get(pk=chore_id)
    if not chore.revert_void_permitted():
        return HttpResponse('', reason='Operation not permitted.', status=403)
    elif chore.voided.who != response.user:
        return HttpResponse('', reason="You didn't void this chore!",
                            status=403)
    else:
        chore.voided.clear()
        return action_response(response.user, chore)

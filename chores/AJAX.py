from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json
import datetime
from chores.models import Chore

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


@login_required()
def sign_up(response, chore_id):
    print('In sign_up view.')
    chore = Chore.objects.get(pk=chore_id)
    if chore.signed_up:
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        # TODO: this code is very close to the stuff used in the sign_off
        # function. Make a separate function.
        # TODO: after making timezone stuff work here make those changes
        # everywhere else.
        return HttpResponse('', reason='{coo} signed up for this chore {tdp}.'\
            .format(coo=chore.signed_up.who.profile.nickname, tdp=\
                timedelta_pretty_print(datetime.datetime.now(pytz.utc)-\
                    chore.signed_up.when)), status=403)
    else:
        chore.signed_up.sign(response.user)
        chore.save()
        # TODO: some repetition here with the chores templates. How to fix?
        # TODO: only use "Sign-off needed!" if we're in the past?
    return HttpResponse(json.dumps({'sign_up_sentence': 'You are signed up.',
        'sign_off_sentence': 'Sign-off needed!'}), status=200)

@login_required()
def sign_off(response, chore_id):
    print('In sign_off view.')
    chore = Chore.objects.get(pk=chore_id)
    if not chore.signed_up:
        # Error: no one has signed up. User should only be able to get here my
        # manually entering a URL.
        return HttpResponse('', reason='No one has signed up for this chore.',
                            status=403)
    if chore.signed_off:
        # Error: someone has already signed up. Return who has signed up and
        # when they signed up. Return an error code so the JavaScript function
        # can display this in an alert.
        return HttpResponse('', reason='{coo} signed off on this chore {tdp}.'\
            .format(coo=chore.signed_off.who.profile.nickname, tpd=\
                timedelta_pretty_print(datetime.datetime.now()-\
                    chore.when_signed_off)), status=403)
    if response.user == chore.signed_up.who:
        # Error: can't sign off on your own chore. Have this pop up in an
        # alert.
        return HttpResponse('', reason="You can't sign off on your own "
                            "chore.", status=403)
    else:
        chore.signed_off.sign(response.user)
        chore.save()
        return HttpResponse(json.dumps({
            'sign_off_sentence': 'You signed off.'}), status=200)

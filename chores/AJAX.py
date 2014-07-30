from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import datetime
import json
from profiles.AJAX import make_form_response
from chores.models import Chore, ChoreSkeleton, ChoreError
from chores.forms import ChoreSkeletonForm, ChoreForm
from chores.views import get_chore_sentences, calculate_balance

#TODO: remove.
from chores.models import Signature
from stewardships.forms import ClassicalStewardshipFormCreator
from django.contrib.auth.models import User

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

def create_function_creator(model=None, model_callable=None, model_form=None,
                            model_form_callable=None):
    #TODO: another permissions test here.
    @login_required
    def create_function(request, model=model, model_callable=model_callable,
                        model_form=model_form,
                        model_form_callable=model_form_callable):
        print('in the edit_function')
        if model is None:
            model = model_callable(request)
        if model_form is None:
            model_form = model_form_callable(request)
        print('model is: {nam}'.format(nam=model.__name__))
        print('model form is: {nam}'.format(nam=model_form.__name__))
        form = model_form(request.POST)
        if form.is_valid():
            print('about to call form.save')
            try:
                form.save(request=request)
            except Exception as e:
                print('error in calling form.save')
                print(e)
                raise e
        return make_form_response(form)
    return create_function

def edit_function_creator(model=None, model_callable=None, model_form=None,
                          model_form_callable=None):
    #TODO: IMPORTANT: check that the person making the object and the object
    #they're editing are in the same co-op.
    #TODO: another permissions test here.
    @login_required()
    def edit_function(request, model=model, model_callable=model_callable,
                      model_form=model_form,
                      model_form_callable=model_form_callable):
        print('in the edit_function')
        try:
            if model is None:
                model = model_callable(request)
            if model_form is None:
                model_form = model_form_callable(request)
            print('model is: {nam}'.format(nam=model.__name__))
            print('model form is: {nam}'.format(nam=model_form.__name__))
        except Exception as e:
            print('error in assigning model and model_form')
            print(e)
            raise e
        print('made it past the first try/except block')
        try:
            object_id = int(getattr(request, request.method)['choice_id'])
        except Exception as e:
            print('error in assigning object_id')
            print(e)
            raise e
        print('about to test request.method')
        if request.method == 'GET':
            print('request method is GET')
            # TODO: error checking here.
            #TODO: no need to assign the actual variable -- just put in render
            #arguments.
            #TODO: make not explaining why the order of operations is slightly
            #different here when compared with `create_function`. We can't
            #create the form without giving it instance (I think).
            try:
                form = model_form(instance=model.objects.get(pk=object_id))
            except Exception as e:
                print('error in making the form')
                print(e)
                raise e
            return render(request, 'form.html', {'form': form})
        elif request.method == 'POST':
            try:
                print('request method is POST')
                form = model_form(request.POST)
                if form.is_valid():
                    old_instance = model.objects.get(pk=object_id)
                    old_instance.delete()
                    new_instance = form.save(commit=True, request=request)
                    new_instance.id = object_id
                    new_instance.save()
                return make_form_response(form)

            except Exception as e:
                print('error in doing the post bit')
                print(e)
                raise e

        return None

    return edit_function

chore_skeleton_create = create_function_creator(model=ChoreSkeleton,
                                                model_form=ChoreSkeletonForm)
chore_skeleton_edit = edit_function_creator(model=ChoreSkeleton,
                                            model_form=ChoreSkeletonForm)

#TODO: split chore editing into one function for individual chores and one for
#bulk creating and deleting.
@login_required()
def chore_create(request):
    #TODO: clean this up.
    print('got to here')
    form = ChoreForm(request.POST)
    print('about to check whether form is valid')
    try:
        form.is_valid()
    except Exception as e:
        print('error in checking whether form was valid')
        print(e)
        raise e
    if form.is_valid():
        print('form is valid')
        #Django (as of version 1.6.5) doesn't permit bulk creation of
        #inherited models, and Chore inherits from Timecard. So we have to do
        #it one-by-one. Haven't managed to get it working with Signatures,
        #either. Guessing a problem with pk? See <https://docs.djangoproject
        #.com/en/dev/ref/models/querysets/#bulk-create>.
        repeat_interval = datetime.timedelta(days=form.cleaned_data[
            'repeat_interval'])
        try:
            for repeat in range(form.cleaned_data['number_of_repeats']):
                shift = repeat*repeat_interval
                chore = Chore.objects.create_blank(
                    skeleton=form.cleaned_data['skeleton'],
                    start_date=form.cleaned_data['start_date']+shift,
                    stop_date=form.cleaned_data['stop_date']+shift,
                )
        except Exception as e:
            print('error in doing chores')
            print(e)
            raise e
    else:
        print('form is not valid')
    return make_form_response(form)

def chore_edit(request):
    raise NotImplementedError

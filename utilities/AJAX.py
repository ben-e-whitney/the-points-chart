from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

import json

def make_form_response(form):
    # TODO: remove all this.
    print('***in make_form_response***')
    if form.errors:
        print({
            'errors': {
                field: ' '.join(form.errors[field]) for field in form.errors if
                field != '__all__'
            },
        })
    if form.non_field_errors():
        print('form non_field_errors: {fe}'.format(fe=form.non_field_errors()))
    print('about to make and return the HttpResponse')
    return HttpResponse(json.dumps({
        #TODO: there should be a better way of doing this.
        'errors': {
            field: ' '.join(form.errors[field]) for field in form.errors if
            field != '__all__'
        },
        'non_field_errors': list(form.non_field_errors())
    }), status=200 if form.is_valid() else 400)

def create_function_creator(model=None, model_callable=None, model_form=None,
                            model_form_callable=None):
    #TODO: another permissions test here.
    @login_required
    def create_function(request, model=model, model_callable=model_callable,
                        model_form=model_form,
                        model_form_callable=model_form_callable):
        print('in the create_function')
        if model is None:
            model = model_callable(request)
        if model_form is None:
            model_form = model_form_callable(request)
        print('model is: {nam}'.format(nam=model.__name__))
        print('model form is: {nam}'.format(nam=model_form.__name__))
        try:
            form = model_form(request.POST)
        except Exception as e:
            print('error in getting the form')
            print(e)
            raise e
        try:
            form.is_valid()
        except Exception as e:
            print('error in checking whether form is valid')
            print(e)
            raise e
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
                          model_form_callable=None, get_id=None):
    if get_id is None:
        get_id = lambda request: int(getattr(request, request.method)[
            'choice_id'])
    #TODO: IMPORTANT: check that the person making the object and the object
    #they're editing are in the same co-op.
    #TODO: another permissions test here.
    @login_required()
    def edit_function(request, model=model, model_callable=model_callable,
                      model_form=model_form,
                      model_form_callable=model_form_callable, get_id=get_id):
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
            object_id = get_id(request)
        except Exception as e:
            print('error in assigning object_id')
            print(e)
            raise e
        print('about to test request.method')
        if request.method == 'GET':
            print('request method is GET')
            try:
                print('working with object {oid}'.format(oid=object_id))
                form = model_form(instance=model.objects.get(pk=object_id))
            except Exception as e:
                print('error in making the form')
                print(e)
                raise e
            #TODO: error checking here.
            #TODO: no need to assign the actual variable -- just put in render
            #arguments.
            #TODO: make not explaining why the order of operations is slightly
            #different here when compared with `create_function`. We can't
            #create the form without giving it instance (I think).
            return render(request, 'form.html', {'form': form})
        elif request.method == 'POST':
            print('request method is POST')
            try:
                form = model_form(request.POST,
                                  instance=model.objects.get(pk=object_id))
            except Exception as e:
                print('error in making the form')
                print(e)
                raise e

            try:
                thing = form.is_valid()
            except Exception as e:
                print('error in calling form.is_valid')
                print(e)
                raise e

            if form.is_valid():
                print('form is valid')
                try:
                    #old_instance = model.objects.get(pk=object_id)
                    #old_instance.delete()
                    new_instance = form.save(commit=False, request=request)
                    new_instance.id = object_id
                    new_instance.save()
                    #old_instance.delete()
                except Exception as e:
                    print('error in trying to replace')
                    print(e)
                    raise e
            else:
                print('form is not valid')
                print(form.errors)
                print(form.non_field_errors())

            return make_form_response(form)
        return None

    return edit_function


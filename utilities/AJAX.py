from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

import json

def make_form_response(form):
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
    #TODO: make this a permission, or make a function for this, or something.
    @login_required
    @user_passes_test(lambda user: user.profile.points_steward)
    def create_function(request, model=model, model_callable=model_callable,
                        model_form=model_form,
                        model_form_callable=model_form_callable):
        if model is None:
            model = model_callable(request)
        if model_form is None:
            model_form = model_form_callable(request)
        form = model_form(request.POST)
        if form.is_valid():
            form.save(request=request)
        return make_form_response(form)
    return create_function

def edit_function_creator(model=None, model_callable=None, model_form=None,
                          model_form_callable=None, get_id=None):
    if get_id is None:
        get_id = lambda request: int(getattr(request, request.method)[
            'choice_id'])
    #TODO: IMPORTANT: check that the person making the object and the object
    #they're editing are in the same co-op.
    #TODO: add some parameter letting us specify whether we want to only allow
    #the steward to make edits. Editing your own profile is the big exception.
    #@user_passes_test(lambda user: user.profile.points_steward)
    @login_required()
    def edit_function(request, model=model, model_callable=model_callable,
                      model_form=model_form,
                      model_form_callable=model_form_callable, get_id=get_id):
        if model is None:
            model = model_callable(request)
        if model_form is None:
            model_form = model_form_callable(request)
        object_id = get_id(request)
        if request.method == 'GET':
            form = model_form(instance=model.objects.get(pk=object_id))
            #TODO: error checking here.
            #TODO: no need to assign the actual variable -- just put in render
            #arguments.
            #TODO: make not explaining why the order of operations is slightly
            #different here when compared with `create_function`. We can't
            #create the form without giving it instance (I think).
            return render(request, 'form.html', {'form': form})
        elif request.method == 'POST':
            form = model_form(request.POST,
                              instance=model.objects.get(pk=object_id))
            if form.is_valid():
                new_instance = form.save(commit=False, request=request)
                new_instance.id = object_id
                new_instance.save()
            return make_form_response(form)

        return None

    return edit_function

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import BLANK_CHOICE_DASH
from django.http import HttpResponse
from django.shortcuts import render

import json

class BasicForm(forms.ModelForm):
    #TODO: docstring out of date.
    """
    Subclass of forms.ModelForm.

    Adds `error_css_class` class variable and extends `save` method to handle
    'request' keyword argument.

    Public methods:
        save
    """

    class Meta:
        pass

    error_css_class = 'form_error'

    def save(self, *args, **kwargs):
        """
        Extends forms.ModelForm.save, allowing for 'request' keyword.

        'request' keyword argument is thrown away if present.
        """
        return super().save(
            *args,
            **{key: value for key, value in kwargs.items() if key != 'request'}
        )

    @staticmethod
    def get_id_from_request(request, id_key='choice_id'):
        return int(getattr(request, request.method).get(id_key))

    def respond_with_errors(self):
        """
        Make response following form submission.
        """
        #TODO: there should be a better way of doing this.
        print('in respond_with_errors')
        return HttpResponse(json.dumps({
            'errors': {
                field: ' '.join(self.errors[field]) for field in self.errors
                    if field != '__all__'
            },
            'non_field_errors': list(self.non_field_errors())
        }), status=200 if self.is_valid() else 400)

    @classmethod
    def create_from_request(cls, request):
        form = cls(request.POST)
        if form.is_valid():
            form.save(request=request)
        return form.respond_with_errors()

    @classmethod
    def edit_from_request(cls, request):
        """
        Edit preexisting object in response to `request`.

        Arguments:
            request -- HTTP request from form submission.
        """
        print('in edit_from_request')
        try:
            object_id = cls.get_id_from_request(request)
        except KeyError as e:
            return HttpResponse('', reason='Request QueryDict has no entry '
                                'with key {key}.'.format(key=e), status=400)
        except ValueError as e:
            return HttpResponse('', reason='Could not interpret object ID: '
                                '{msg}.'.format(msg=e), status=400)
        print('got object_id')
        if request.method not in ('GET', 'POST'):
            return HttpResponse('', status=405)
        else:
            print('request.method is {rem}'.format(rem=request.method))
            try:
                instance = cls.Meta.model.objects.get(pk=object_id)
            except ObjectDoesNotExist:
                return HttpResponse('', reason='Not object found with ID '
                                    '{oid}'.format(oid=object_id), status=404)
            print('made instance')
            if request.method == 'GET':
                print('method is GET')
                try:
                    x = render(request, 'form.html',
                                  {'form': cls(instance=instance)})
                except Exception as e:
                    print(e)
                    raise e
                return x
            else:
                print('method is POST')
                #`request.method` is 'POST'.
                form = cls(request.POST, instance=instance)
                print('got form')
                if form.is_valid():
                    print('form is valid')
                    new_instance = form.save(commit=False, request=request)
                    new_instance.id = object_id
                    new_instance.save()
                print('passing to respond_with_errors now')
                return form.respond_with_errors()

def cycle_field_creator(coop):
    """
    Find `coop`'s cycles and return a form field with those cycles as choices.

    Arguments:
        coop -- Group whose cycles we are interested in.

    Return a CharField with the current cycles as choices. No initial or
    default choice is made.
    """
    CYCLE_CHOICES = tuple(
        (int(cycle_num), 'Cycle {num} ({stadat} to {stodat})'
             .format(num=cycle_num, stadat=cycle_start.isoformat(),
                     stodat=cycle_stop.isoformat()))
        for cycle_num, cycle_start, cycle_stop in coop.profile.cycles()
    )
    #I have found no way to set a default (not just initial) value. See
    #<https://docs.djangoproject.com/en/dev/ref/forms/fields/#initial>.
    return forms.CharField(widget=forms.Select(choices=CYCLE_CHOICES))

def cooper_field_creator(coop, blank=False, required=True):
    """
    Find `coop`'s members and return a form field with those people as choices.

    Arguments:
        coop -- Group whose members we are interested in.

    Keyword arguments:
        blank -- If True, a blank choice is added to the form field. If False,
            no action is taken.
        required -- Passed as a keyword argument to CharField constructor.

    Return a CharField with the current members as choices. No initial or
    default choice is made.
    """
    COOPER_CHOICES = [
        (cooper.id, cooper.profile.nickname)
        for cooper in coop.user_set.filter(is_active=True).prefetch_related(
            'profile').order_by('profile__nickname')
    ]
    if blank:
        COOPER_CHOICES = BLANK_CHOICE_DASH+COOPER_CHOICES
    cooper = forms.CharField(required=required,
                             widget=forms.Select(choices=COOPER_CHOICES))
    return cooper

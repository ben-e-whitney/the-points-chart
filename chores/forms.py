from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.fields import BLANK_CHOICE_DASH

from chores.models import ChoreSkeleton, Chore, Timecard, Signature, ChoreError
from utilities.forms import BasicForm, cooper_field_creator

class ChoreSkeletonForm(BasicForm):
    class Meta:
        model = ChoreSkeleton
        fields = ['short_name', 'short_description', 'point_value',
                  'start_time', 'end_time']

    def save(self, commit=True, request=None, **kwargs):
        skeleton = super().save(commit=False)
        skeleton.coop = request.user.profile.coop
        if commit:
            skeleton.save()
        return skeleton

def ChoreFormCreator(request):
    coop = request.user.profile.coop

    class ChoreForm(BasicForm):
        #repeat_interval = forms.IntegerField(validators=[MinValueValidator(1)])
        #number_of_repeats = forms.IntegerField(validators=[MinValueValidator(1)])
        #Blank/null (TODO: which is it?) values will be converted.
        signed_up  = cooper_field_creator(coop, blank=True, required=False)
        signed_off = cooper_field_creator(coop, blank=True, required=False)
        voided     = cooper_field_creator(coop, blank=True, required=False)
        class Meta:
            #TODO: maybe this shouldn't be a ModelForm if we're creating
            #multiple objects at once?
            model = Chore
            fields = ['skeleton', 'start_date', 'stop_date', 'signed_up',
                      'signed_off', 'voided']
            widgets = {
                field: forms.DateInput(attrs={'class': 'date_picker'})
                for field in ('start_date', 'stop_date')
            }

        def clean_signature_creator(field_name):

            def clean_field(self):
                field_value = self.cleaned_data.get(field_name)
                clean_value = Signature()
                if field_value != '':
                    clean_value.sign(User.objects.get(pk=field_value),
                                     commit=False)
                return clean_value

            return clean_field

        clean_signed_up  = clean_signature_creator('signed_up')
        clean_signed_off = clean_signature_creator('signed_off')
        clean_voided     = clean_signature_creator('voided')

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                for sig_name in ('signed_up', 'signed_off', 'voided'):
                    try:
                        cooper_id = getattr(instance, sig_name).who.id
                    except AttributeError:
                        cooper_id = BLANK_CHOICE_DASH[0][0]
                    initial.update({sig_name: cooper_id})
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def clean(self):
            cleaned_data = super().clean()
            #TODO: add code to allow for possibility of failed comparison.
            if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
                # TODO: in Django 1.7 you can use `self.add_error()`. See
                # <https://docs.djangoproject.com/en/dev/ref/forms/api/
                # #django.forms.Form.add_error>.
                raise ValidationError('Stop date cannot be before start date.')
            timecard = Timecard(
                start_date=cleaned_data.get('start_date'),
                stop_date=cleaned_data.get('start_date'),
                signed_up=cleaned_data.get('signed_up'),
                signed_off=cleaned_data.get('signed_off'),
                voided=cleaned_data.get('voided'),
            )
            coopers = {}
            #TODO: this is all necessary because the form seems to validate the
            #remaining fields even if a ValidationError is thrown here. Ideally
            #we could define these fields in such a way that the form didn't
            #associate them with the model fields; otherwise maybe we
            #could change this form from being a ModelForm at all.
            for field_name in ('signed_up', 'signed_off', 'voided'):
                signature = cleaned_data.get(field_name)
                user = signature.who
                if user is not None:
                    signature.revert(user, commit=False)
                signature.save()
                coopers.update({field_name: user})
            #The order is important here.
            for field_name, method_name in zip(
                ('signed_up', 'signed_off', 'voided'),
                ('sign_up', 'sign_off', 'void')
            ):
                signature = cleaned_data.get(field_name)
                user = coopers.get(field_name)
                if user is not None:
                    try:
                        getattr(timecard, method_name)(user)
                    except ChoreError as e:
                        raise ValidationError(e)

                cleaned_data.update({
                    field_name: getattr(timecard, field_name)
                })

            #TODO: seems like '' is getting translated to `None`? Why? See
            #<https://docs.djangoproject.com/en/dev/ref/models/fields/>.
            #TODO: back to testing against ''.

            return cleaned_data

        def save(self, *args, **kwargs):
            request = kwargs.pop('request', None)
            commit = kwargs.get('commit', True)
            kwargs.update({'commit': False})
            chore = super().save(*args, **kwargs)
            for field_name in ('signed_up', 'signed_off', 'voided'):
                setattr(chore, field_name, self.cleaned_data[field_name])
                if commit:
                    getattr(chore, field_name).save()
            if commit:
                chore.save()
            return chore

    return ChoreForm

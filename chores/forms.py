from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models.fields import BLANK_CHOICE_DASH

from chores.models import ChoreSkeleton, Chore, Timecard, Signature, ChoreError
from utilities.forms import BasicForm, cooper_field_creator

class ChoreSkeletonForm(BasicForm):
    class Meta:
        model = ChoreSkeleton
        fields = ['short_name', 'short_description', 'point_value',
                  'start_time', 'end_time', 'url']

    def save(self, commit=True, request=None, **kwargs):
        skeleton = super().save(commit=False)
        skeleton.coop = request.user.profile.coop
        if commit:
            skeleton.save()
        return skeleton

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].label = 'URL'

def ChoreFormCreator(request):
    coop = request.user.profile.coop

    class ChoreForm(BasicForm):
        #Null values will be converted.
        signed_up  = cooper_field_creator(coop, required=False)
        signed_off = cooper_field_creator(coop, required=False)
        voided     = cooper_field_creator(coop, required=False)
        class Meta:
            model = Chore
            fields = ['skeleton', 'start_date', 'stop_date', 'signed_up',
                      'signed_off', 'voided']
            widgets = {
                field: forms.DateInput(attrs={'class': 'date_picker'})
                for field in ('start_date', 'stop_date')
            }

        def clean_signature_creator(field_name):

            def clean_signature(self):
                user = self.cleaned_data.get(field_name)
                signature = Signature()
                if user is None:
                    signature.save()
                else:
                    #TODO: check that user is in the coop here?
                    signature.sign(user)
                return signature

            return clean_signature

        clean_signed_up  = clean_signature_creator('signed_up')
        clean_signed_off = clean_signature_creator('signed_off')
        clean_voided     = clean_signature_creator('voided')

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                for sig_name in ('signed_up', 'signed_off', 'voided'):
                    try:
                        user_id = getattr(instance, sig_name).who.id
                    except AttributeError:
                        user_id = BLANK_CHOICE_DASH[0][0]
                    initial.update({sig_name: user_id})
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def clean(self):
            cleaned_data = super().clean()
            necessary_keys = ('skeleton', 'start_date', 'stop_date',
                              'signed_up', 'signed_off', 'voided')
            #Only proceed with additional validation if all the necessary
            #fields have values.
            if any(key not in cleaned_data for key in necessary_keys):
                return cleaned_data
            #TODO: either this code needs to be repeated elsewhere (e.g. for
            #the Stewardship form), or we need to somehow pull this out into a
            #function or superclass or something.
            try:
                proper_ordering = (cleaned_data['stop_date'] >=
                    cleaned_data['start_date'])
            except TypeError:
                self.add_error('start_date', ValidationError(
                    'Comparison of start and stop dates failed.'))
            if not proper_ordering:
                self.add_error('stop_date', ValidationError(
                    'Stop date cannot be before start date.'))

            timecard = Timecard(
                start_date=cleaned_data.get('start_date'),
                stop_date=cleaned_data.get('start_date'),
                signed_up=cleaned_data.get('signed_up'),
                signed_off=cleaned_data.get('signed_off'),
                voided=cleaned_data.get('voided'),
            )
            signers = {}
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
                signers.update({field_name: user})
            #The order is important here.
            for field_name, method_name in zip(
                ('signed_up', 'signed_off', 'voided'),
                ('sign_up', 'sign_off', 'void')
            ):
                signature = cleaned_data.get(field_name)
                user = signers.get(field_name)
                if user is not None:
                    try:
                        getattr(timecard, method_name)(user, commit=False)
                    except ChoreError as e:
                        raise ValidationError(e)

                cleaned_data.update({
                    field_name: getattr(timecard, field_name)
                })
            return cleaned_data

        def destruct(self):
            for sig_name in ('signed_up', 'signed_off', 'voided'):
                self.cleaned_data.get(sig_name).delete()
            return None

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

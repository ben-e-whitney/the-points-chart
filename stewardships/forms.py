from django import forms

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.fields import BLANK_CHOICE_DASH

from chores.models import Signature
from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange, BenefitChangeSkeleton)
from utilities.forms import (BasicForm, cycle_field_creator,
    cooper_field_creator)

class ClassicalStewardshipSkeletonForm(BasicForm):

    class Meta:
        model = StewardshipSkeleton
        fields = ['short_name', 'short_description', 'point_value']

    #TODO: change these kwargs to work the same as in `__init__`. Is it OK to
    #use 'commit' as an argument keyword?
    def save(self, commit=True, request=None, **kwargs):
        skeleton = super().save(commit=False)
        skeleton.coop = request.user.profile.coop
        skeleton.category = StewardshipSkeleton.STEWARDSHIP
        if commit:
            skeleton.save()
        return skeleton

# TODO: for all these, consider doing start and stop cycles. Barely leaning
# towards keeping them as start and stop dates internally.
def ClassicalStewardshipFormCreator(request):
    coop = request.user.profile.coop
    class ClassicalStewardshipForm(BasicForm):
        cooper = cooper_field_creator(coop)
        class Meta:
            model = Stewardship
            fields = ['skeleton', 'cooper', 'start_date', 'stop_date']
            widgets = {
                field: forms.DateInput(attrs={'class': 'date_picker'})
                for field in ('start_date', 'stop_date')
            }

        #TODO: consider factoring out all the common stuff in these __init__
        #functions.
        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                initial.update({'cooper': instance.signed_up.who.id})
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def clean(self):
            cleaned_data = super().clean()
            #TODO: put in error detection here for if the comparison fails.
            #Maybe this would get caught by cleaning for each field, but if you
            #just directly hit '/stewardships/actions/create/
            #classical_stewardship' then you get an error.
            if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
                raise ValidationError('Stop date cannot be before start date.')
            return cleaned_data

        def save(self, commit=True, request=None, **kwargs):
            stewardship = super().save(commit=False)
            stewardship.make_signatures(commit=False,
                signed_up=User.objects.get(pk=self.cleaned_data['cooper']),
                signed_off=None, voided=None)
            if commit:
                stewardship.save()
            return stewardship

    return ClassicalStewardshipForm

def LoanFormCreator(request):
    coop = request.user.profile.coop

    class LoanForm(BasicForm):
        cooper = cooper_field_creator(coop)
        cycle = cycle_field_creator(coop)
        point_value = forms.IntegerField()
        short_description = forms.CharField(widget=forms.Textarea)

        class Meta:
            model = Stewardship
            fields = ['cooper', 'cycle', 'point_value', 'short_description']

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                initial.update({
                    'cooper': instance.signed_up.who.id,
                    'cycle': coop.profile.get_cycle(
                        start_date=instance.start_date,
                        stop_date=instance.stop_date),
                    'point_value': instance.skeleton.point_value,
                    'short_description': instance.skeleton.short_description,
                })
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def save(self, commit=True, request=None, **kwargs):
            loan = super().save(commit=False)
            skeleton = StewardshipSkeleton(
                coop=request.user.profile.coop,
                category=StewardshipSkeleton.LOAN,
                short_name='Loan',
                point_value=self.cleaned_data['point_value'],
                short_description=self.cleaned_data['short_description']
            )
            skeleton.save()
            loan.skeleton = skeleton
            loan.make_signatures(commit=False,
                signed_up=User.objects.get(pk=self.cleaned_data['cooper']),
                signed_off=None, voided=None)
            loan.start_date, loan.stop_date = coop.profile.get_cycle_endpoints(
                # TODO: find where the data is stored as an integer.
                int(self.cleaned_data.get('cycle'))
            )
            if commit:
                loan.save()
            return loan

    return LoanForm

def SpecialPointsFormCreator(request):
    coop = request.user.profile.coop

    class SpecialPointsForm(BasicForm):
        cooper = cooper_field_creator(coop)
        point_value = forms.IntegerField()
        short_description = forms.CharField(widget=forms.Textarea)

        class Meta:
            model = Stewardship
            fields = ['cooper', 'start_date', 'point_value',
                      'short_description']
            widgets = {
                'start_date': forms.DateInput(attrs={'class': 'date_picker'})
            }

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                initial.update({
                    'cooper': instance.signed_up.who.id,
                    'point_value': instance.skeleton.point_value,
                    'short_description': instance.skeleton.short_description,
                })
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def save(self, commit=True, request=None, **kwargs):
            special_points = super().save(commit=False)
            skeleton = StewardshipSkeleton(
                coop=request.user.profile.coop,
                category=StewardshipSkeleton.SPECIAL_POINTS,
                short_name='Special Points',
                point_value=self.cleaned_data['point_value'],
                short_description=self.cleaned_data['short_description']
            )
            skeleton.save()
            special_points.skeleton = skeleton
            special_points.make_signatures(commit=False,
                signed_up=User.objects.get(pk=self.cleaned_data['cooper']),
                signed_off=None, voided=None)
            special_points.stop_date = special_points.start_date
            if commit:
                special_points.save()
            return special_points

    return SpecialPointsForm

def AbsenceFormCreator(request):
    coop = request.user.profile.coop

    class AbsenceForm(BasicForm):
        cooper = cooper_field_creator(coop)
        short_description = forms.CharField(widget=forms.Textarea)

        class Meta:
            model = Absence
            fields = ['cooper', 'start_date', 'stop_date', 'short_description']
            # TODO: can we define this when not using these as fields? Would be
            # good to use as a TimecardForm class or something.
            widgets = {
                field: forms.DateInput(attrs={'class': 'date_picker'})
                for field in ('start_date', 'stop_date')
            }

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                initial.update({
                    'cooper': instance.signed_up.who.id,
                    'short_description': instance.skeleton.short_description,
                })
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def clean(self):
            cleaned_data = super().clean()
            if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
                raise ValidationError('Stop date cannot be before start date.')
            return cleaned_data

        def save(self, commit=True, request=None, **kwargs):
            absence = super().save(commit=False)
            skeleton = BenefitChangeSkeleton(
                coop=request.user.profile.coop,
                short_name='Absence',
                short_description=self.cleaned_data['short_description']
            )
            skeleton.save()
            absence.skeleton = skeleton
            absence.make_signatures(commit=False,
                signed_up=User.objects.get(pk=self.cleaned_data['cooper']),
                signed_off=None, voided=None)
            if commit:
                absence.save()
            return absence

    return AbsenceForm

def ShareChangeFormCreator(request):
    coop = request.user.profile.coop

    class ShareChangeForm(BasicForm):
        cooper = cooper_field_creator(coop)
        cycle = cycle_field_creator(coop)
        short_description = forms.CharField(widget=forms.Textarea)

        class Meta:
            model = ShareChange
            fields = ['cooper', 'cycle', 'share_change', 'short_description']

        def __init__(self, *args, **kwargs):
            instance = kwargs.get('instance', None)
            if instance is not None:
                initial = kwargs.get('initial', {})
                initial.update({
                    'cooper': instance.signed_up.who.id,
                    'cycle': coop.profile.get_cycle(
                        start_date=instance.start_date,
                        stop_date=instance.stop_date),
                    'short_description': instance.skeleton.short_description,
                })
                kwargs.update({'initial': initial})
            super().__init__(*args, **kwargs)

        def save(self, commit=True, request=None, **kwargs):
            share_change = super().save(commit=False)
            skeleton = BenefitChangeSkeleton(
                coop=request.user.profile.coop,
                short_name='Share Change',
                short_description=self.cleaned_data['short_description']
            )
            skeleton.save()
            share_change.skeleton = skeleton
            share_change.make_signatures(commit=False,
                signed_up=User.objects.get(pk=self.cleaned_data['cooper']),
                signed_off=None, voided=None)
            share_change.start_date, share_change.stop_date = (
                coop.profile.get_cycle_endpoints(
                    int(self.cleaned_data.get('cycle'))
                )
            )
            if commit:
                share_change.save()
            return share_change

    return ShareChangeForm

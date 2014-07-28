from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from chores.models import Signature
from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange, BenefitChangeSkeleton)
from chores.forms import BasicForm

def cycle_field_creator(coop):
    CYCLE_CHOICES = tuple(
        (int(cycle_num), 'Cycle {num} ({stadat} to {stodat})'
             .format(num=cycle_num, stadat=cycle_start.isoformat(),
                     stodat=cycle_stop.isoformat()))
        for cycle_num, cycle_start, cycle_stop in coop.profile.cycles()
    )
    # TODO: figure out if default is allowed here, or how to do it.
    cycle = forms.CharField(widget=forms.Select(choices=CYCLE_CHOICES))
    return cycle

def cooper_field_creator(coop):
    COOPER_CHOICES = tuple((cooper.id, cooper.profile.nickname) for cooper in
                           coop.user_set.all())
    cooper = forms.CharField(widget=forms.Select(choices=COOPER_CHOICES))
    return cooper

class ClassicalStewardshipSkeletonForm(BasicForm):

    class Meta:
        model = StewardshipSkeleton
        fields = ['short_name', 'short_description', 'point_value']

    def create_object(self, request=None):
        skeleton = self.save(commit=False)
        skeleton.coop = request.user.profile.coop
        skeleton.category = StewardshipSkeleton.STEWARDSHIP
        skeleton.save()
        return self

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

        def clean(self):
            cleaned_data = super().clean()
            if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
                print('bad stop date: {sd}'.format(
                    sd=cleaned_data.get('stop_date')))
                print('bad start date: {sd}'.format(
                    sd=cleaned_data.get('start_date')))
                raise ValidationError('Stop date cannot be before start date.')
            return cleaned_data

        def create_object(self, request=None):
            print('in ClassicalStewardshipsForm.create_object; form is valid')
            try:
                stewardship = self.save(commit=False)
            except Exception as e:
                print('error in saving stewardships without committing')
                print(e)
                raise e
            signed_up = Signature()
            signed_up.sign(User.objects.get(pk=self.data['cooper']))
            stewardship.signed_up = signed_up
            for signature_name in ('signed_off', 'voided'):
                signature = Signature()
                signature.save()
                setattr(stewardship, signature_name, signature)
            print('got to right before saving')
            try:
                stewardship.save()
            except Exception as e:
                print('error in saving stewardship')
                print(e)
                raise e
            return self

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

        def create_object(self, request=None):
            skeleton = StewardshipSkeleton(
                coop=request.user.profile.coop,
                category=StewardshipSkeleton.LOAN,
                short_name='Loan',
                point_value=self.data['point_value'],
                short_description=self.data['short_description']
            )
            skeleton.save()
            loan = self.save(commit=False)
            loan.skeleton = skeleton
            # TODO: could make a `create_blank`-esque method for the Timecard
            # QuerySet that would make this smoother, and hopefully reuse it for
            # Chores. Might not work.
            signed_up = Signature()
            signed_up.sign(User.objects.get(pk=self.data['cooper']))
            loan.signed_up = signed_up
            for signature_name in ('signed_off', 'voided'):
                signature = Signature()
                signature.save()
                setattr(loan, signature_name, signature)
            loan.start_date, loan.stop_date = coop.profile.get_cycle_endpoints(
                # TODO: find where the data is stored as an integer.
                int(self.cleaned_data.get('cycle'))
            )
            loan.save()
            return self

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

        def create_object(self, request=None):
            print('in SpecialPointsForm.create_object; form is valid')
            skeleton = StewardshipSkeleton(
                coop=request.user.profile.coop,
                category=StewardshipSkeleton.SPECIAL_POINTS,
                short_name='Special Points',
                point_value=self.data['point_value'],
                short_description=self.data['short_description']
            )
            skeleton.save()
            special_points = self.save(commit=False)
            special_points.skeleton = skeleton
            signed_up = Signature()
            signed_up.sign(User.objects.get(pk=self.data['cooper']))
            special_points.signed_up = signed_up
            for signature_name in ('signed_off', 'voided'):
                signature = Signature()
                signature.save()
                setattr(special_points, signature_name, signature)
            print(special_points.__dict__)
            special_points.stop_date = special_points.start_date
            special_points.save()
            return self

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
            # good to use as a TimeCardForm class or ssomething.
            widgets = {
                field: forms.DateInput(attrs={'class': 'date_picker'})
                for field in ('start_date', 'stop_date')
            }

        def clean(self):
            cleaned_data = super().clean()
            if cleaned_data.get('stop_date') < cleaned_data.get('start_date'):
                raise ValidationError('Stop date cannot be before start date.')
            return cleaned_data

        def create_object(self, request=None):
            # First create the skeleton, and then the actual absence.
            skeleton = BenefitChangeSkeleton(
                coop=request.user.profile.coop,
                short_name='Absence',
                short_description=self.data['short_description']
            )
            skeleton.save()
            absence = self.save(commit=False)
            absence.skeleton = skeleton
            # TODO: make this into a function.
            signed_up = Signature()
            signed_up.sign(User.objects.get(pk=self.data['cooper']))
            absence.signed_up = signed_up
            for signature_name in ('signed_off', 'voided'):
                signature = Signature()
                signature.save()
                setattr(absence, signature_name, signature)
            print('about to save')
            absence.save()
            return self

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

        def create_object(self, request=None):
            # First create the skeleton, and then the actual absence.
            skeleton = BenefitChangeSkeleton(
                coop=request.user.profile.coop,
                short_name='Share Change',
                short_description=self.data['short_description']
            )
            skeleton.save()
            share_change = self.save(commit=False)
            share_change.skeleton = skeleton
            # TODO: make this into a function.
            signed_up = Signature()
            signed_up.sign(User.objects.get(pk=self.data['cooper']))
            share_change.signed_up = signed_up
            for signature in ('signed_off', 'voided'):
                sig = Signature()
                sig.save()
                setattr(share_change, signature, sig)
            share_change.start_date, share_change.stop_date = (
                coop.profile.get_cycle_endpoints(
                    int(self.cleaned_data.get('cycle'))
                )
            )
            share_change.save()
            return self

    return ShareChangeForm

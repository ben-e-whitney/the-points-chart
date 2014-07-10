from django import forms

from stewardships.models import (StewardshipSkeleton, Stewardship, Absence,
    ShareChange)
from chores.forms import BasicForm, ChoreSkeletonForm, ChoreForm

def cycle_field_creator(coop):
    CYCLE_CHOICES = tuple(
        (int(cycle_num),
         'Cycle {num} ({stadat} to {stodat})'.format(num=cycle_num,
             stadat=cycle_start.isoformat(), stodat=cycle_stop.isoformat()))
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

# TODO: figure out some inheritance for this mess.
def SingletonFormCreator(coop):
    class SingletonForm(BasicForm):
        cooper = cooper_field_creator(coop)
        short_description = forms.CharField(widget=forms.Textarea)
        class Meta:
            model = Stewardship
            fields = ['cooper', 'short_description']
    return SingletonForm

class ClassicalStewardshipSkeletonForm(BasicForm):
    class Meta:
        model = StewardshipSkeleton
        fields = ['short_name', 'short_description', 'point_value']

# TODO: for all these, consider doing start and stop cycles. Barely leaning
# towards keeping them as start and stop dates internally.
def ClassicalStewardshipFormCreator(coop):
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
                raise ValidationError('Stop date cannot be before start date.')
            return cleaned_data

    return ClassicalStewardshipForm

def SpecialPointsFormCreator(coop):
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
    return SpecialPointsForm

def LoanFormCreator(coop):
    class LoanForm(BasicForm):
        cooper = cooper_field_creator(coop)
        cycle  = cycle_field_creator(coop)
        point_value = forms.IntegerField()
        short_description = forms.CharField(widget=forms.Textarea)
        class Meta:
            model = Stewardship
            fields = ['cooper', 'cycle', 'point_value', 'short_description']
    return LoanForm

def AbsenceFormCreator(coop):
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

    return AbsenceForm

def ShareChangeFormCreator(coop):
    class ShareChangeForm(BasicForm):
        cooper = cooper_field_creator(coop)
        cycle = cycle_field_creator(coop)
        short_description = forms.CharField(widget=forms.Textarea)
        class Meta:
            model = ShareChange
            fields = ['cooper', 'cycle', 'share_change', 'short_description']
    return ShareChangeForm

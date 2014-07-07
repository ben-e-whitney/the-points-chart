from django.db import models

# Create your models here.
from django import forms

from chores.models import Skeleton, Timecard, ChoreQuerySet
from model_utils.managers import PassThroughManager

# TODO: not sure whether these being so skimpy is a good or bad sign.

class StewardshipQuerySet(ChoreQuerySet):

    '''
    Modification of `ChoreQuerySet` to allow for a different understanding of
    when a Stewardship falls inside a time window. See `in_window`
    documetation.
    '''

    def in_window(self, window_start_date, window_stop_date):
        '''
        Overrides superclass method. Performs same general function.

        Arguments:
            window_start_date -- Beginning of time window.
            window_stop_date  -- End of the time window.

        Return those chores which overlap with the given window. That is,
        return those chores which start before or on `window_stop_date` and
        end after or on `window_start_date`. (We assume that the stewardship
        starts before or on the date it ends.) The results are ordered by start
        date.
        '''
        return self.filter(
            start_date__lte=window_stop_date,
            stop_date__gte=window_start_date
        ).order_by('start_date')

class StewardshipSkeleton(Skeleton):
    STEWARDSHIP = 'STEW'
    SPECIAL_POINTS = 'SPEC'
    LOAN = 'LOAN'
    CATEGORY_CHOICES = (
        (STEWARDSHIP, 'Stewardship'),
        (SPECIAL_POINTS, 'Special Points'),
        (LOAN, 'Loan')
    )
    category = models.CharField(max_length=4, choices=CATEGORY_CHOICES,
                                default=STEWARDSHIP)
    # Per cycle.
    point_value = models.PositiveSmallIntegerField()

class ClassicalStewardshipSkeletonForm(forms.ModelForm):
    class Meta:
        model = StewardshipSkeleton
        fields = ['short_name', 'short_description', 'point_value']
    error_css_class = 'form_error'

class Stewardship(Timecard):
    skeleton = models.ForeignKey(StewardshipSkeleton,
                                 related_name='stewardship')
    objects = PassThroughManager.for_queryset_class(StewardshipQuerySet)()

    def __str__(self):
        return '{cn} on {dat}'.format(cn=self.skeleton.short_name,
                                   dat=self.start_date.isoformat())

    def __radd__(self, other):
        return self.skeleton.point_value+other

class ClassicalStewardshipForm(forms.ModelForm):
    class Meta:
        model = Stewardship
        fields = ['skeleton', 'start_date', 'stop_date']
    error_css_class = 'form_error'

class SpecialPointsForm(forms.ModelForm):
    short_description = forms.CharField(widget=forms.Textarea)
    point_value = forms.IntegerField()
    class Meta:
        model = Stewardship
        # fields = ['short_description', 'start_date' 'point_value']
        fields = ['short_description', 'start_date']
    error_css_class = 'form_error'

def cycle_field_creator(coop):
    CYCLE_CHOICES = tuple(
        ((cycle_num, cycle_start, cycle_stop),
         'Cycle {num} ({stadat} to {stodat})'.format(num=cycle_num,
             stadat=cycle_start.isoformat(), stodat=cycle_stop.isoformat()))
        for cycle_num, cycle_start, cycle_stop in coop.profile.cycles()
    )
    # TODO: figure out if default is allowed here, or how to do it.
    cycle = forms.CharField(widget=forms.Select(choices=CYCLE_CHOICES))
    return cycle

def LoanFormCreator(coop):
    class LoanForm(forms.ModelForm):
        point_value = forms.IntegerField()
        short_description = forms.CharField(widget=forms.Textarea)
        cycle = cycle_field_creator(coop)
        class Meta:
            model = Stewardship
            # TODO: see point in `SpecialPointsForm`.
            fields = ['short_description', 'cycle', 'point_value']
        error_css_class = 'form_error'
    return LoanForm

# For these objects, changes are made for the cycle(s) spanning the date range.
# For example, if a user is marked out for two days, then their load will be
# reduced by the appropriate fraction of the total points for the cycle(s) (not
# days) during which they were absent.
class BenefitChangeSkeleton(Skeleton):
    pass

# TODO: figure out how `in_window` should behave here. Think it should only
# check `start_date`, to allow for `start_date` and `stop_date` to actually
# behave as the start and stop date. Get that going, because then you can get
# rid of `days_gone`.
class Absence(Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton, related_name='absence')
    # TODO: Superfluous. Use `self.start_date` and `self.stop_date` instead.
    days_gone = models.PositiveSmallIntegerField()
    objects = PassThroughManager.for_queryset_class(StewardshipQuerySet)()

    def __radd__(self, other):
        return self.days_gone+other

class AbsenceForm(forms.ModelForm):
    short_description = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Absence
        # TODO: Also need a picker for all the co-opers.
        # Calculate `days_gone` using `start_date` and `stop_date`.
        fields = ['short_description', 'start_date', 'stop_date']
    error_css_class = 'form_error'

class ShareChange(Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton,
                                 related_name='share_change')
    share_change = models.DecimalField(max_digits=3, decimal_places=2)
    objects = PassThroughManager.for_queryset_class(StewardshipQuerySet)()

    def __radd__(self, other):
        return self.share_change+other

def ShareChangeFormCreator(coop):
    class ShareChangeForm(forms.ModelForm):
        short_description = forms.CharField(widget=forms.Textarea)
        cycle = cycle_field_creator(coop)
        class Meta:
            model = ShareChange
            fields = ['short_description', 'cycle', 'share_change']
        error_css_class = 'form_error'
    return ShareChangeForm

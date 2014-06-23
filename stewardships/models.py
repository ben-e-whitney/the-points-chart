from django.db import models

# Create your models here.

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

class Stewardship(Timecard):
    skeleton = models.ForeignKey(StewardshipSkeleton,
                                 related_name='stewardship')
    objects = PassThroughManager.for_queryset_class(StewardshipQuerySet)()

# For these objects, changes are made for the cycle(s) spanning the date range.
# For example, if a user is marked out for two days, then their load will be
# reduced by the appropriate fraction of the total points for the cycle(s) (not
# days) during which they were absent.
class BenefitChangeSkeleton(Skeleton):
    note = models.TextField()

class Absence(Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton, related_name='absence')
    # TODO: Superfluous. Use `self.start_date` and `self.stop_date` instead.
    days_gone = models.PositiveSmallIntegerField()
    objects = PassThroughManager.for_queryset_class(StewardshipQuerySet)()

class ShareChange(Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton,
                                 related_name='share_change')
    share_change = models.DecimalField(max_digits=3, decimal_places=2)
    objects = PassThroughManager.for_queryset_class(StewardshipQuerySet)()

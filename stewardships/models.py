from django.db import models

# Create your models here.

from chores.models import Skeleton, Timecard, TimeWindowManager as chore_TWM

# TODO: not sure whether these being so skimpy is a good or bad sign.

class TimeWindowManager(chore_TWM):

    '''
    Modification of `chore_TWM` to allow for different understanding of when a
    Stewardship falls inside a time window. See `in_window` documetation.
    '''

    def in_window(self, coop, start_date, stop_date):
        '''
        Overrides superclass method. Provides the same functionality.

        Arguments:
            coop       -- Group whose chores we are interested in.
            start_date -- Beginning of time window.
            stop_date  -- End of the time window.

        Changes from the superclass method are enclosed in asterisks.
        Return an iterator yielding those chores which belong to the given
        `coop`, which start before or on `stop_date`, and which end after or
        on `start_date`. The results are ordered by starting date.
        '''
        return self.filter(
           skeleton__coop=coop,
            start_date__lte=start_date,
            stop_date__gte=stop_date
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
    objects = TimeWindowManager()

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
    objects = TimeWindowManager()

class ShareChange(Timecard):
    skeleton = models.ForeignKey(BenefitChangeSkeleton,
                                 related_name='share_change')
    share_change = models.DecimalField(max_digits=3, decimal_places=2)
    objects = TimeWindowManager()

from django.db import models, connection

# Create your models here.

from django.contrib.auth.models import User, Group
# See <http://www.dabapps.com/blog/higher-level-query-api-django-orm/>.
from model_utils.managers import PassThroughManager

import datetime
import itertools

class ChoreQuerySet(models.query.QuerySet):

    def for_coop(self, coop):
        '''
        Query the model database and return an iterator of Chore instances.

        Arguments:
            coop -- Group whose chores we are interested in.

        Return an iterator yielding those chores which belong to `coop`.
        '''
        return self.filter(skeleton__coop=coop)

    def in_window(self, window_start_date, window_stop_date):
        '''
        Query the model database and return an iterator of Chore instances.

        Arguments:
            window_start_date -- Beginning of time window.
            window_stop_date  -- End of the time window.

        Return those chores which start after or on `window_start_date` and
        before or on `window_stop_date`. We do not impose any requirements on
        the stop date to avoid that problem of chores that straddle multiple
        cycles not being considered to fall in any one of those cycles. The
        results are ordered by start date.
        '''
        return self.filter(
            start_date__gte=window_start_date,
            start_date__lte=window_stop_date
        ).order_by('start_date')

    def signature_check(self, cooper, bool_, sig_name):
        '''
        Query the model database and return an iterator of Chore instances.

        Arguments:
            cooper   -- A User or `None`.
            bool_    -- Boolean determining whether we want Signature to have
                been signed.
            sig_name -- Name of the Signature field we are checking against.

        Return an iterator yielding those chores which have (if `bool_`) or
        haven't (if `not bool_`) their `sig_name` Signature signed. If `cooper`
        is None, we don't make any additional demands. If `cooper' is a User,
        we ask that it be this User that has signed. To be clear:
            self.signature_check(False, cooper, 'signed_up')
        will return all chores except those on which `cooper` has signed off.
        '''
        kwargs = {sig_name+'__who': cooper}
        # No cooper specified, so we're just asking generally.
        if cooper is None:
            if bool_:
                return self.exclude(**kwargs)
            else:
                return self.filter(**kwargs)
        # If a cooper is specified, we want that person to be the one having
        # signed up.
        else:
            if bool_:
                return self.filter(**kwargs)
            else:
                return self.exclude(**kwargs)

    def signed_up(self, cooper, bool_):
        '''
        Calls `signature_check` with signature name 'signed_up'.
        '''
        return self.signature_check(cooper, bool_, 'signed_up')

    def signed_off(self, cooper, bool_):
        '''
        Calls `signature_check` with signature name 'signed_off'.
        '''
        return self.signature_check(cooper, bool_, 'signed_off')

    def voided(self, cooper, bool_):
        '''
        Calls `signature_check` with signature name 'voided'.
        '''
        return self.signature_check(cooper, bool_, 'voided')

class Signature(models.Model):
    who = models.ForeignKey(User, null=True, blank=True,
                            related_name='signature')
    when = models.DateTimeField(null=True, blank=True)

    def __bool__(self):
        return self.who is not None

    def __str__(self):
        if not self:
            return 'empty Signature'
        else:
            return 'Signature of {use} at {dat}'.format(use=self.who,
                                                        dat=self.when)
    def sign(self, user):
        self.who = user
        self.when = datetime.datetime.now()

class Timecard(models.Model):
    # TODO: making this into an abstract class causes validation to fail
    # (complaints about ForeignKeys again). Would be nice to figure it out.
    start_date = models.DateField()
    stop_date  = models.DateField()
    # TODO: here or elsewhere, look into ForeignKey limit_choices_to feature.
    # See <https://docs.djangoproject.com/en/dev/ref/models/fields/#foreignkey>.
    signed_up = models.ForeignKey(Signature, related_name='timecard_signed_up')
    signed_off = models.ForeignKey(Signature,
                                   related_name='timecard_signed_off')
    voided = models.ForeignKey(Signature, related_name='timecard_voided')
    def __str__(self):
        person = self.signed_up.who.profile.nickname \
                if self.signed_up else 'no one'
        coop = self.skeleton.coop.name if hasattr(self, 'skeleton') \
            else '<NO CO-OP SET>'
        return '{cn} at {co} with {per} signed up'\
            .format(cn=self.__class__.__name__, co=coop, per=person)

class Skeleton(models.Model):
    class Meta:
        abstract = True
    # TODO: Adding a related name here caused an error. It looks like it was
    # complaining that two different subclasses of this class had the same
    # accessor/related field/something. If you end up needing this you might
    # need to move the ForeignKey statement to the subclasses, or do something
    # like
    #   coop = models.ForeignKey(Group, self.__class__.__name__)
    # which is I think roughly what the default is anyway.
    coop = models.ForeignKey(Group)
    short_name = models.CharField(max_length=2**6)
    short_description = models.TextField()
    def __str__(self):
        return '{sn} Skeleton at {co}'.format(sn=self.short_name,
                                     co=self.coop.name)

class ChoreSkeleton(Skeleton):
    point_value = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time   = models.TimeField()

class Chore(Timecard):
    skeleton = models.ForeignKey(ChoreSkeleton, related_name='chore')
    objects = PassThroughManager.for_queryset_class(ChoreQuerySet)()
    def __str__(self):
        return '{cn} on {da} at {co}'.format(cn=self.skeleton.short_name,
                             da=self.start_date, co=self.skeleton.coop.name)

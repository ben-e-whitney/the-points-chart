from django.db import models, connection

# Create your models here.

from django.contrib.auth.models import User, Group

import datetime
import itertools

class TimeWindowManager(models.Manager):

    '''
    Extends models.Manager, adding a few filtering methods for convenience.
    '''

    def in_window(self, coop, start_date, stop_date):
        '''
        Query the model database and return an iterator of Chore instances.

        Arguments:
            coop       -- Group whose chores we are interested in.
            start_date -- Beginning of time window.
            stop_date  -- End of the time window.

        Return an iterator yielding those chores which belong to the given
        `coop`, which start after or on `start_date`, and which end before or
        on `stop_date`. The results are ordered by starting date.
        '''

        # TODO: check whether you can first filter by skeleton__coop and sort,
        # and optionally later filter by start and stop dates (while preserving
        # the ordering).
        if start_date is None or stop_date is None:
            return self.filter(skeleton__coop=coop).order_by('start_date')
        else:
            return self.filter(
               skeleton__coop=coop,
               start_date__lte=start_date,
               stop_date__gte=stop_date,
            ).order_by('start_date')

    def signed(self, *args, signatures=None, users=itertools.repeat(None),
               desired_booleans=itertools.repeat(True)):
        # TODO: make other docstrings like this. See
        # <http://legacy.python.org/dev/peps/pep-0257/.
        '''
        Calls `in_window` with given arguments and filters based on Signatures.

        Keyword arguments:
            signatures       -- Iterable that yields attributes that
                `self.model` has as ForeignKeys to a Signature object.
            users            -- Iterable yielding a User (for when we care
                whether a given User has signed the corresponding Signature) or
                `None` (for when we only care whether any User has signed it).
            desired_booleans -- Iterable that yields Booleans we want the
                comparison involving the User and the Signature to return. See
                `acceptable` method for details.

        Returns an iterator of `self.model` object matches.
        Careful: if `signatures` is `['voided']`, `users` is `['None']`, and
        `desired_booleans` is ['True'], then chores which some User (*not*
        no/'None' User) has voided will be returned.
        '''

        def acceptable(chore):
            '''
            Judges whether chore satisfies criteria and returns a Boolean.

            Arguments:
                chore -- Chore (or similar) instance which is to be tested.

            `chore` is judged acceptable if each Signature object in
            `signatures` is signed off or signed off by the corresponding User.
            '''
            test_results = []
            for sig, user, desired_bool in zip(signatures, users,
                                               desired_booleans):
                if user is None:
                    result = bool(getattr(chore, sig))
                else:
                    result = getattr(chore, sig).who == user
                test_results.append(result)
            return all(test_results)

        # TODO: decide what this should return!
        return list(chore for chore in self.in_window(*args)
                    if acceptable(chore))

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
    objects = TimeWindowManager()
    def __str__(self):
        return '{cn} on {da} at {co}'.format(cn=self.skeleton.short_name,
                             da=self.start_date, co=self.skeleton.coop.name)

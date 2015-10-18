from django.db import models, connection

from django.contrib.auth.models import User, Group
from django.utils import timezone
# See <http://www.dabapps.com/blog/higher-level-query-api-django-orm/>.
from model_utils.managers import PassThroughManager

import datetime
import pytz
import functools
from utilities import timedelta

# TODO: how do we tie the `signed_up` property, the `sign_up_permission` etc.
# methods, 'sign up' as a verb, the JavaScript function names, etc.?

#TODO: make these settings in the Group profile.
MINIMUM_DAYS_BEFORE_TO_REVERT_SIGN_UP = 2
REVERT_SIGN_UP_GRACE_PERIOD_HOURS = 1

class ChoreError(Exception):
    pass

class ChoreSkeletonQuerySet(models.query.QuerySet):

    def for_coop(self, coop):
        return self.filter(coop=coop)

class ChoreQuerySet(models.query.QuerySet):
    def for_coop(self, coop):
        chore_skeletons = set(ChoreSkeleton.objects.for_coop(coop=coop))
        return self.filter(skeleton__in=chore_skeletons)

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

    #TODO: is this used yet?
    def create_blank(self, skeleton=None, start_date=None, stop_date=None):
        signatures = {}
        for signature_name in ('signed_up', 'signed_off', 'voided'):
            signature = Signature()
            signature.save()
            signatures.update({signature_name: signature})
        chore = Chore(skeleton=skeleton, start_date=start_date,
                      stop_date=stop_date, **signatures)
        chore.save()
        return chore

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
    def sign(self, user, *args, **kwargs):
        commit = kwargs.get('commit', True)
        self.who = user
        self.when = timezone.now()
        if commit:
            self.save()

    def revert(self, user, *args, **kwargs):
        commit = kwargs.get('commit', True)
        # Placeholder for any future logic.
        self.clear(*args, **kwargs)

    def clear(self, *args, **kwargs):
        commit = kwargs.get('commit', True)
        self.who = None
        self.when = None
        if commit:
            self.save()

class Timecard(models.Model):
    updated = models.DateTimeField()
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

    def save(self, *args, **kwargs):
        for signature_name in ('signed_up', 'signed_off', 'voided'):
            getattr(self, signature_name).save()
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    # TODO: figure out what exactly this is being used for. Decide whether you
    # really want to use `__str__`, or maybe something else.
    def __repr__(self):
        person = self.signed_up.who.profile.nickname \
                if self.signed_up else 'no one'
        coop = self.skeleton.coop.name if hasattr(self, 'skeleton') \
            else '<NO CO-OP SET>'
        return '{cn} at {co} with {per} signed up'\
            .format(cn=self.__class__.__name__, co=coop, per=person)

    def __str__(self):
        raise NotImplementedError

    def __radd__(self, other):
        raise NotImplementedError

    def make_signatures(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            signature = Signature()
            if value:
                signature.sign(value, commit=False)
            signature.save()
            setattr(self, key, signature)
        if commit:
            self.save()

    # Methods for use in the following. If you end up doing stuff like this,
    # could prepend the function names with however many underscores.
    def resolved(self):
        return self.signed_off or self.voided

    def completed_successfully(self):
        return self.signed_up and self.signed_off and not self.voided

    # TODO: use timedelta.in_interval for these two? Should we pay attention to
    # anything other than days?
    #TODO: can't we get the coop from the chore?
    def in_the_future(self, coop):
        return self.start_date > coop.profile.today()

    def in_the_past(self, coop):
        return self.start_date < coop.profile.today()

    def in_grace_period(self):
        return timedelta.in_interval(0, timezone.now()-self.signed_up.when,
            REVERT_SIGN_UP_GRACE_PERIOD_HOURS, unit='hours')

    #TODO: add optional argument for current time. Will save regenerating it.
    def too_close_to_revert_sign_up(self):
        return timedelta.in_interval(0, self.start_date-timezone.now().date(),
                                     MINIMUM_DAYS_BEFORE_TO_REVERT_SIGN_UP)

    def get_scoop_message(self, user, attribute, verb):
        owner = getattr(self, attribute).who
        return '{coo} {ver} this chore {tdp}.'.format(
            coo='You' if owner == user else owner.profile.nickname,
            ver=verb,
            # TODO: make sure that you're not making an assumption about the
            # timezone here.
            # TODO: error can happen here if you have a Signature with a
            # co-oper but no datetime (will be subtracting a datetime with
            # `None`. Figure out what to do.
            tdp=(timedelta.pretty_str(timezone.now()-
                 getattr(self, attribute).when))
        )

    # Could make the argument that voiding should be allowed even when someone
    # has signed off (overriding that person). For now we can void a signed up/
    # signed off chore by reverting the sign-off and then voiding, or by using
    # the admin interface.
    # TODO: are there going to be timezone problems here?

    def actor_commit_wrap(f):
        def inner(self, user, *args, **kwargs):
            commit = kwargs.get('commit', True)
            output = f(self, user, *args, **kwargs)
            if commit:
                self.save()
            return output
        return inner

    @actor_commit_wrap
    def sign_up(self, user, *args, **kwargs):
        testing = kwargs.pop('testing', False)
        if self.voided:
            raise ChoreError(self.get_scoop_message(user, 'voided', 'voided'))
        if self.signed_up:
            raise ChoreError(self.get_scoop_message(user, 'signed_up',
                                                    'signed up for'))
        if not testing:
            self.signed_up.sign(user, *args, **kwargs)

    @actor_commit_wrap
    def sign_off(self, user, *args, **kwargs):
        testing = kwargs.pop('testing', False)
        if not self.signed_up:
            raise ChoreError('No one has signed up for that chore.')
        if self.signed_up.who == user:
            raise ChoreError("You can't sign off on your own chore.")
        if self.in_the_future(user.profile.coop):
            raise ChoreError("You can't sign off on a chore before it has "
                             "been done.")
        if self.signed_off:
            raise ChoreError(self.get_scoop_message(user, 'signed_off',
                                                    'signed off on'))
        if self.voided:
            raise ChoreError(self.get_scoop_message(user, 'voided', 'voided'))
        if not testing:
            self.signed_off.sign(user, *args, **kwargs)

    @actor_commit_wrap
    def void(self, user, *args, **kwargs):
        testing = kwargs.pop('testing', False)
        if self.signed_up.who != user and not user.profile.points_steward:
            raise ChoreError("You can't void a chore that isn't yours.")
        if self.in_the_future(user.profile.coop):
            raise ChoreError("You can't void a chore before it has been done.")
        if self.voided:
            raise ChoreError(self.get_scoop_message(user, 'voided', 'voided'))
        if self.signed_off:
            raise ChoreError(self.get_scoop_message(user, 'signed_off',
                                                    'signed off on'))
        if not testing:
            self.voided.sign(user, *args, **kwargs)

    @actor_commit_wrap
    def revert_sign_up(self, user, *args, **kwargs):
        #TODO: include grace period for this, too.
        testing = kwargs.pop('testing', False)
        if not self.signed_up.who == user:
            raise ChoreError("You didn't sign up for that chore.")
        if not self.signed_up:
            raise ChoreError("No one has signed up for that chore.")
        if self.signed_off:
            raise ChoreError(self.get_scoop_message(user, 'signed_off',
                                                    'signed off'))
        if self.voided:
            raise ChoreError(self.get_scoop_message(user, 'voided', 'voided'))
        if self.too_close_to_revert_sign_up() and not self.in_grace_period():
            steward = user.profile.coop.profile.points_steward().profile.nickname
            raise ChoreError("It's too close to the chore. Talk to {ste} if "
                             "you really can't do it.".format(ste=steward))
        if self.in_the_past(user.profile.coop) and not self.in_grace_period():
            raise ChoreError("The chore's already past. Void instead.")
        if not testing:
            self.signed_up.revert(user, *args, **kwargs)

    @actor_commit_wrap
    def revert_sign_off(self, user, *args, **kwargs):
        testing = kwargs.pop('testing', False)
        if not self.signed_up:
            raise ChoreError("No one is signed off on that chore.")
        if self.signed_off.who != user:
            raise ChoreError("You didn't sign off on that chore.")
        if not testing:
            self.signed_off.revert(user, *args, **kwargs)

    @actor_commit_wrap
    def revert_void(self, user, *args, **kwargs):
        testing = kwargs.pop('testing', False)
        if not self.voided:
            raise ChoreError("That chore hasn't been voided.")
        if self.voided.who != user:
            raise ChoreError("You didn't void that chore.")
        if not testing:
            self.voided.revert(user, *args, **kwargs)

    def methods_enabled(self, user):
        methods = []
        for method in ('sign_up', 'revert_sign_up', 'sign_off',
                       'revert_sign_off', 'void', 'revert_void'):
            try:
                getattr(self, method)(user, commit=False, testing=True)
                methods.append(method)
            except ChoreError:
                pass
        return methods

    def find_CSS_classes(self, user):
        '''
        Sets flags relating to `chores` that are read by the template. The
        actual formatting information is kept in a CSS file.
        '''
        # TODO: seems like an example of somewhere we want to use the
        # GroupProfile time zone.
        current_date = timezone.now().date()
        old_count = len(connection.queries)
        methods_enabled = self.methods_enabled(user)
        css_classes = {
            'needs_sign_up': 'sign_up' in methods_enabled,
            'needs_sign_off': 'sign_off' in methods_enabled,
            'completed_successfully': self.completed_successfully(),
            'voided': self.voided,
            'user_signed_up': user == self.signed_up.who,
            'user_signed_off': user == self.signed_off.who,
            'user_voided': user == self.voided.who
        }
        return ' '.join([key for key, bool_ in css_classes.items() if bool_])

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
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return '{sn} Skeleton at {co}'.format(sn=self.short_name,
                                     co=self.coop.name)

class ChoreSkeleton(Skeleton):
    point_value = models.PositiveSmallIntegerField()
    # TODO: consider changing the name of this to `stop_time` to match with
    # `start_date` and `stop_date`.
    start_time = models.TimeField()
    end_time   = models.TimeField()
    objects = PassThroughManager.for_queryset_class(ChoreSkeletonQuerySet)()
    sort_index = models.IntegerField(default=0)

#TODO: add this in later.
#class ChoreSchedule(models.Model):
#    skeleton = models.ForeignKey(ChoreSkeleton, related_name='schedule')
#    objects = PassThroughManager.for_queryset_class(ChoreQuerySet)()
#    #TODO: start cycle and stop cycle.
#    #TODO: days

class Chore(Timecard):
    skeleton = models.ForeignKey(ChoreSkeleton, related_name='chore')
    objects = PassThroughManager.for_queryset_class(ChoreQuerySet)()

    def __str__(self):
        return '{cn} on {dat}'.format(cn=self.skeleton.short_name,
                                   dat=self.start_date.isoformat())

    def __radd__(self, other):
        return self.skeleton.point_value+other


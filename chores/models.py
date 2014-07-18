from django.db import models, connection

# Create your models here.

from django.contrib.auth.models import User, Group
# See <http://www.dabapps.com/blog/higher-level-query-api-django-orm/>.
from model_utils.managers import PassThroughManager

import datetime
import pytz
import functools
from chores import timedelta

# TODO: how do we tie the `signed_up` property, the `sign_up_permission` etc.
# methods, 'sign up' as a verb, the JavaScript function names, etc.?

class ChoreError(Exception):
    pass

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
        self.save()

    # TODO: maybe we should save here and not in `clear`?
    def revert(self, user):
        # Placeholder for any future logic.
        self.clear()

    def clear(self):
        self.who = None
        self.when = None
        self.save()

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

    # Methods for use in the following. If you end up doing stuff like this,
    # could prepend the function names with however many underscores.
    def resolved(self):
        return self.signed_off or self.voided

    def completed_successfully(self):
        return self.signed_up and self.signed_off and not self.voided

    def in_the_future(self):
        comparison_date = datetime.date.today()
        return self.start_date > comparison_date

    def get_scoop_message(self, user, attribute, verb):
        owner = getattr(self, attribute).who
        return '{coo} {ver} this chore {tdp}.'.format(
            coo='You' if owner == user else owner.profile.nickname,
            ver=verb,
            # TODO: make sure that you're not making an assumption about the
            # timezone here. TODO: this was `datetime.datetime.now(pytz.utc)`.
            # Removing `pytz.utc` both to make it work and for a reminder that
            # we have to resolve this.
            # TODO: error can happen here if you have a Signature with a
            # co-oper but no datetime (will be subtracting a datetime with
            # `None`. Figure out what to do.
            # TODO: commenting out to get the rest running. Need to fix later.
            tdp=None
            # (timedelta.pretty_print(datetime.datetime.now(pytz.utc)-
                # getattr(self, attribute).when))
        )

    # Could make the argument that voiding should be allowed even when someone
    # has signed off (overriding that person). For now we can void a signed up/
    # signed off chore by reverting the sign-off and then voiding, or by using
    # the admin interface.
    # TODO: are there going to be timezone problems here?

    def permission_creator(conditions, potential_msgs):
        # TODO: mark in docstring that `conditions`/`potential_msgs` should be
        # ordered according to decreasing priority.
        def permission(self, user):
            for condition, potential_msg in zip(conditions, potential_msgs):
                # TODO: adapt this so that condition need not be callable. This
                # might not be possible, since I don't think you have a notion
                # of `self` whenever these are compiled, or whatever. Would
                # need to wrap them in another method? Tired.
                if condition(self, user):
                    if callable(potential_msg):
                        message = potential_msg(self, user)
                    else:
                        message = potential_msg
                    return {'boolean': False, 'message': message}
            return {'boolean': True, 'message': ''}
        return permission

    # TODO: change 'sign_up' and 'sign_off' to 'sign-up' and 'sign-off'?
    sign_up_permission = permission_creator(
        [
            lambda self, user: self.voided,
            lambda self, user: self.signed_up
        ], [
            lambda self, user: self.get_scoop_message(user, 'voided',
                                                      'voided'),
            lambda self, user: self.get_scoop_message(user, 'signed_up',
                                             'signed up for')
        ]
    )
    sign_off_permission = permission_creator(
        [
            lambda self, user: not self.signed_up,
            lambda self, user: self.signed_up.who == user,
            lambda self, user: self.in_the_future(),
            lambda self, user: self.signed_off,
            lambda self, user: self.voided
        ], [
            'No one has signed up for that chore.',
            "You can't sign off on your own chore.",
            "You can't sign off on a chore before it has been done.",
            lambda self, user: self.get_scoop_message(user, 'signed_off',
                                             'signed off on'),
            lambda self, user: self.get_scoop_message(user, 'voided',
                                                      'voided')
        ]
    )
    void_permission = permission_creator(
        [
            lambda self, user: self.in_the_future(),
            lambda self, user: self.voided,
            lambda self, user: self.signed_off
        ], [
            "You can't void a chore before it has been done.",
            lambda self, user: self.get_scoop_message(user, 'voided',
                                                      'voided'),
            lambda self, user: self.get_scoop_message(user, 'signed_off',
                                             'signed off on')
        ]
    )
    revert_sign_up_permission = permission_creator(
        [
            lambda self, user: self.signed_up.who != user,
            lambda self, user: (self.start_date-datetime.date.today() <
                                datetime.timedelta(days=2)),
            lambda self, user: self.voided,
            lambda self, user: self.signed_off
        ], [
            "You didn't sign up for that chore.",
            ("It's too close to the chore. Talk to {ste} if you really can't "
             'do it.').format(ste=None),
            lambda self, user: self.get_scoop_message(user, 'voided',
                                                     'voided'),
            lambda self, user: self.get_scoop_message(user, 'signed_off',
                                                      'signed off')
        ]
    )
    revert_sign_off_permission = permission_creator(
        [lambda self, user: self.signed_off.who != user],
        ["You didn't sign off on that chore."])
    revert_void_permission = permission_creator(
        [lambda self, user: self.voided.who != user],
        ["You didn't void that chore."])

    def actor_creator(permission_method_name, signature_name, action_name):
        def actor(self, user):
            permission = getattr(self, permission_method_name)(user)
            # raise TypeError(permission)
            if permission['boolean']:
                getattr(getattr(self, signature_name), action_name)(user)
            else:
                permission.update({'status': 403})
                raise ChoreError(permission)
        return actor

    # TODO: should we be using functools for all of this, then? Or maybe for
    # none of it?
    signer_creator   = functools.partial(actor_creator, action_name='sign')
    reverter_creator = functools.partial(actor_creator, action_name='revert')
    sign_up  = signer_creator('sign_up_permission', 'signed_up')
    sign_off = signer_creator('sign_off_permission', 'signed_off')
    void     = signer_creator('void_permission', 'voided')
    revert_sign_up  = reverter_creator('revert_sign_up_permission', 'signed_up')
    revert_sign_off = reverter_creator('revert_sign_off_permission',
                                       'signed_off')
    revert_void     = reverter_creator('revert_void_permission', 'voided')

    def find_CSS_classes(self, user):
        '''
        Sets flags relating to `chores` that are read by the template. The
        actual formatting information is kept in a CSS file.
        '''
        current_date = datetime.date.today()
        css_classes = {
            # TODO: names are outdated. Need to fix!
            'needs_sign_up': self.sign_up_permission(user)['boolean'],
            'needs_sign_off': self.sign_off_permission(user)['boolean'],
            'completed_successfully': self.completed_successfully(),
            'voided': self.revert_void_permission(user)['boolean'],
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

    def __str__(self):
        return '{sn} Skeleton at {co}'.format(sn=self.short_name,
                                     co=self.coop.name)

class ChoreSkeleton(Skeleton):
    point_value = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    # TODO: consider changing the name of this to `stop_time` to match with
    # `start_date` and `stop_date`.
    end_time   = models.TimeField()

class Chore(Timecard):
    skeleton = models.ForeignKey(ChoreSkeleton, related_name='chore')
    objects = PassThroughManager.for_queryset_class(ChoreQuerySet)()

    def __str__(self):
        return '{cn} on {dat}'.format(cn=self.skeleton.short_name,
                                   dat=self.start_date.isoformat())

    def __radd__(self, other):
        return self.skeleton.point_value+other


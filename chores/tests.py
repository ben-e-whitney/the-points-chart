from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.utils import timezone

import string
import random
import datetime
import pytz

from chores.models import (ChoreSkeleton, Chore, ChoreError,
    MINIMUM_DAYS_BEFORE_TO_REVERT_SIGN_UP, REVERT_SIGN_UP_GRACE_PERIOD_HOURS)
from profiles.models import UserProfile, GroupProfile

def random_letters(num):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(num))

def random_time():
    return datetime.time(random.randint(0, 23), random.randint(0, 59))

def random_date():
    return datetime.date(
        random.randint(1950, 2050),
        random.randint(1, 12),
        random.randint(1, 20)
    )

def default_to_test_coop(f):
    def inner(*args, **kwargs):
        if 'coop' not in kwargs.keys():
            # `args[0]` will be `self`.
            kwargs['coop'] = args[0].coop
        return f(*args, **kwargs)
    return inner

class ChoreTestCase(TestCase):

    def setUp(self):
        self.coop = Group(name='Test')
        self.coop.save()
        self.coop_profile = GroupProfile(
            group=self.coop,
            short_name='The Co-op',
            short_description='Co-op used for unit tests.',
            full_name='The Test Co-op',
            start_date=datetime.date.today(),
            stop_date=datetime.date.today()+datetime.timedelta(days=100),
            cycle_length=14,
            release_buffer=4,
            time_zone=pytz.UTC
        )
        self.coop_profile.save()
        return None

    @default_to_test_coop
    def make_user(self, coop=None):
        user = User.objects.create_user(
            username=random_letters(16),
            email='{local}@{domain}.com'.format(local=random_letters(8),
                                                domain=random_letters(8)),
            password=random_letters(32)
        )
        profile = UserProfile(
            user=user,
            coop=coop,
            nickname=random_letters(8),
            first_name=user.username.capitalize(),
            middle_name=random_letters(16),
            last_name=random_letters(16),
            email_address=user.email,
            presence=coop.profile.cycle_length,
            share=1,
            public_calendar=True,
            points_steward=False,
        )
        profile.save()
        coop.user_set.add(user)
        return user

    @default_to_test_coop
    def make_chore_skeleton(self, coop=None):
        skeleton = ChoreSkeleton(
            coop=coop,
            short_name=random_letters(4),
            short_description=random_letters(32),
            point_value=random.randint(1, 10),
            start_time=random_time(),
            end_time=random_time()
        )
        skeleton.save()
        return skeleton

    def make_chore(self, skeleton=None, start_date=None, stop_date=None):
        if start_date is None:
            start_date = random_date()
        if stop_date is None:
            stop_date = start_date
        chore = Chore.objects.create_blank(
            skeleton=skeleton,
            start_date=start_date,
            stop_date=stop_date
        )
        return chore

    def test_bad_sign_up(self):
        skeleton = self.make_chore_skeleton()
        chore_to_void = self.make_chore(skeleton)
        chore_to_sign_up = self.make_chore(skeleton)
        user = self.make_user()
        voiding_user = self.make_user()
        copycat_user = self.make_user()

        with self.assertRaises(ChoreError):
            chore_to_void.void(voiding_user)
            chore_to_void.sign_up(user)

        with self.assertRaises(ChoreError):
            chore_to_sign_up.sign_up(user)
            chore_to_sign_up.sign_up(copycat_user)

        return None

    def test_bad_sign_off(self):
        skeleton = self.make_chore_skeleton()
        future_date = timezone.now().date()+datetime.timedelta(days=1)
        past_date = timezone.now().date()+datetime.timedelta(days=-1)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            user = self.make_user()
            chore.sign_off(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            voiding_user = self.make_user()
            user = self.make_user()
            chore.void(voiding_user)
            chore.sign_off(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_up_user = self.make_user()
            signing_off_user = self.make_user()
            copycat_signing_off_user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.sign_off(signing_off_user)
            chore.sign_off(copycat_signing_off_user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            user = self.make_user()
            chore.sign_up(user)
            chore.sign_off(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=future_date)
            signing_up_user = self.make_user()
            signing_off_user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.sign_off(signing_off_user)

        return None

    def test_bad_void(self):
        skeleton = self.make_chore_skeleton()
        future_date = timezone.now().date()+datetime.timedelta(days=1)
        past_date = timezone.now().date()+datetime.timedelta(days=-1)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_up_user = self.make_user()
            voiding_user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.void(voiding_user)

        #This should raise no exceptions.
        try:
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_up_user = self.make_user()
            points_steward_user = self.make_user()
            points_steward_user.profile.points_steward = True
            points_steward_user.profile.save()
            chore.sign_up(signing_up_user)
            chore.void(points_steward_user)
        except ChoreError as e:
            self.fail("Points steward couldn't void a chore.")

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=future_date)
            user = self.make_user()
            chore.void(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            user = self.make_user()
            signing_up_user = self.make_user()
            signing_off_user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.sign_off(signing_off_user)
            chore.void(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            user = self.make_user()
            signing_up_user = self.make_user()
            voiding_user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.void(voiding_user)
            chore.void(user)

        return None

    def test_bad_revert_sign_up(self):
        skeleton = self.make_chore_skeleton()
        future_date = timezone.now().date()+datetime.timedelta(days=1)
        past_date = timezone.now().date()+datetime.timedelta(days=-1)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_up_user = self.make_user()
            user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.revert_sign_up(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            voiding_user = self.make_user()
            user = self.make_user()
            chore.sign_up(user)
            chore.void(voiding_user)
            chore.revert_sign_up(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_off_user = self.make_user()
            user = self.make_user()
            chore.sign_up(user)
            chore.sign_off(signing_off_user)
            chore.revert_sign_up(user)

        with self.assertRaises(ChoreError):
            close_date = timezone.now().date()-datetime.timedelta(
                days=MINIMUM_DAYS_BEFORE_TO_REVERT_SIGN_UP-1)
            chore = self.make_chore(skeleton=skeleton, start_date=close_date)
            chore.sign_up(user)
            # TODO: should we also be checking that certain behavior is
            # permitted? For example, that no error is thrown when the signed
            # up time is not shifted?
            chore.signed_up.when -= datetime.timedelta(
                hours=REVERT_SIGN_UP_GRACE_PERIOD_HOURS+1)
            chore.revert_sign_up(user)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            user = self.make_user()
            chore.sign_up(user)
            chore.signed_up.when -= datetime.timedelta(
                hours=REVERT_SIGN_UP_GRACE_PERIOD_HOURS+1)
            chore.revert_sign_up(user)

        return None

    def test_bad_revert_sign_off(self):
        skeleton = self.make_chore_skeleton()
        future_date = timezone.now().date()+datetime.timedelta(days=1)
        past_date = timezone.now().date()+datetime.timedelta(days=-1)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_up_user = self.make_user()
            signing_off_user = self.make_user()
            user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.sign_off(signing_off_user)
            chore.revert_sign_off(user)

        return None

    def test_bad_revert_void(self):
        skeleton = self.make_chore_skeleton()
        future_date = timezone.now().date()+datetime.timedelta(days=1)
        past_date = timezone.now().date()+datetime.timedelta(days=-1)

        with self.assertRaises(ChoreError):
            chore = self.make_chore(skeleton=skeleton, start_date=past_date)
            signing_up_user = self.make_user()
            voiding_user = self.make_user()
            user = self.make_user()
            chore.sign_up(signing_up_user)
            chore.void(voiding_user)
            chore.revert_void(user)

        return None


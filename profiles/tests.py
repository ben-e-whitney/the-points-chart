from django.test import TestCase
from django.contrib.auth.models import Group

from profiles.models import GroupProfile

import datetime
import pytz

class GroupProfileTestCase(TestCase):
    def setUp(self):
        self.coop = Group(name='Test')
        self.coop.save()
        self.coop_profile = GroupProfile(
            group=self.coop,
            short_name='The Co-op',
            short_description='Co-op used for unit tests.',
            full_name='The Test Co-op',
            start_date=datetime.date(2000, 1, 1),
            stop_date = datetime.date(2000, 2, 1),
            cycle_length=3,
            release_buffer=1,
            time_zone=pytz.UTC
        )
        self.coop_profile.save()
        return None

    def test_find_cycle(self):
        test_pairs = {
                datetime.date(2000, 1, 1): 1,
                datetime.date(2000, 1, 3): 1,
                datetime.date(2000, 1, 4): 2,
                datetime.date(2000, 1, 5): 2,
                datetime.date(2000, 2, 1): 11,
        }
        bad_dates = (datetime.date(1999, 12, 31), datetime.date(2000, 2, 2))
        for date, cycle_num in test_pairs.items():
            self.assertEqual(self.coop_profile.find_cycle(date=date),
                    cycle_num)
        with self.assertRaises(ValueError):
            for date in bad_dates:
                self.coop_profile.find_cycle(date=date)
        return None

    def test_cycles(self):
        self.assertEqual(len(tuple(self.coop_profile.cycles())), 11)
        self.assertEqual(tuple(self.coop_profile.cycles(
            start_date=datetime.date(2000, 1, 1),
            stop_date=datetime.date(2000, 1, 3))),
            (('1', datetime.date(2000, 1, 1), datetime.date(2000, 1, 3)),))
        self.assertEqual(tuple(self.coop_profile.cycles(
            start_date=datetime.date(2000, 1, 1),
            stop_date=datetime.date(2000, 1, 4))),
            (('1', datetime.date(2000, 1, 1), datetime.date(2000, 1, 3)),
                ('2', datetime.date(2000, 1, 4), datetime.date(2000, 1, 6)),))
        with self.assertRaises(ValueError):
            tuple(self.coop_profile.cycles(
                start_date=datetime.date(2000, 1, 2),
                stop_date=datetime.date(2000, 1, 1)))
        return None

    def test_get_cycle_and_get_cycle_endpoints(self):
        test_pairs = {
                1: (datetime.date(2000, 1, 1), datetime.date(2000, 1, 3)),
                2: (datetime.date(2000, 1, 4), datetime.date(2000, 1, 6)),
                3: (datetime.date(2000, 1, 7), datetime.date(2000, 1, 9)),
        }
        bad_endpoints = (
                (datetime.date(1999, 12, 31), datetime.date(2000, 1, 3)),
                (datetime.date(2000, 1, 31), datetime.date(2000, 2, 2)),
                (datetime.date(2000, 1, 2), datetime.date(2000, 1, 5)),
                (datetime.date(2000, 1, 1), datetime.date(2000, 1, 2)),
        )
        bad_cycle_nums = (-1, 12)
        for cycle_num, endpoints in test_pairs.items():
            self.assertEqual(self.coop_profile.get_cycle_endpoints(cycle_num),
                    endpoints)
            self.assertEqual(self.coop_profile.get_cycle(
                start_date=endpoints[0], stop_date=endpoints[1]), cycle_num)
        for endpoints in bad_endpoints:
            with self.assertRaises(ValueError):
                self.coop_profile.get_cycle(start_date=endpoints[0],
                        stop_date=endpoints[1])
        for cycle_num in bad_cycle_nums:
            with self.assertRaises(ValueError):
                self.coop_profile.get_cycle_endpoints(cycle_num)
        return None

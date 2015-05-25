from django.test import TestCase
from utilities.views import format_balance
from utilities.timedelta import in_interval, pretty_print, daterange

import datetime
import decimal

class FormatBalanceTestCase(TestCase):
    def setUp(self):
        self.endpoints = (-float('inf'), 0, float('inf'))
        self.possible_CSS_classes = ('negative', 'positive')

    def test_format_balance(self):
        test_pairs = {
            (-1, 1): 'negative',
            (1, 1): 'positive',
            (-1, -1): 'positive',
            (1, -1): 'negative',
        }
        for (balance, load), CSS_class in test_pairs.items():
            self.assertEqual(
                format_balance(balance=decimal.Decimal(balance),
                               load=decimal.Decimal(load),
                               endpoints=self.endpoints,
                               possible_CSS_classes=self.possible_CSS_classes),
                {
                    'value': float(balance),
                    'formatted_value': '{sgn}{bal}'.format(bal=abs(balance),
                        sgn= '+' if balance > 0 else '−'),
                    'html_title': 'Exact value: {val}'.format(val=balance),
                    'CSS_class': 'balance '+CSS_class,
                }
            )

class TimeDeltaTestCase(TestCase):

    def test_in_interval(self):
        self.assertTrue(in_interval(1, datetime.timedelta(days=2), 3))
        self.assertTrue(in_interval(2, datetime.timedelta(days=2), 3))
        self.assertFalse(in_interval(1, datetime.timedelta(days=2), 2))
        self.assertFalse(in_interval(59, datetime.timedelta(minutes=1), 61)),
        self.assertTrue(in_interval(59, datetime.timedelta(minutes=1), 61,
                                    unit='seconds'))
        return None

    def test_pretty_print(self):
        test_pairs = (
            ({'days': -3}, '3 days from now'),
            ({'minutes': -30}, '30 minutes from now'),
            ({'hours': 1}, '1 hours ago'),
            ({'seconds': 5}, '5 seconds ago'),
            ({'days': -3.1}, '3 days from now'),
            ({'seconds': 5.9}, '5 seconds ago'),
        )
        for kwargs, output in test_pairs:
            self.assertEqual(pretty_print(datetime.timedelta(**kwargs)),
                             output)
        return None

    def test_daterange(self):
        self.assertEqual(365, len(tuple(daterange(datetime.date(1999, 1, 1),
                                                  datetime.date(2000, 1, 1)))))
        #2000 was a leap year.
        self.assertEqual(366, len(tuple(daterange(datetime.date(2000, 1, 1),
                                                  datetime.date(2001, 1, 1)))))
        self.assertEqual(
            tuple(daterange(datetime.date(2000, 1, 1),
                            datetime.date(2000, 1, 3))),
            (datetime.date(2000, 1, 1), datetime.date(2000, 1, 2))
        )
        self.assertEqual(
            tuple(daterange(datetime.date(2000, 1, 1),
                            datetime.date(2000, 1, 3), inclusive=True)),
            (datetime.date(2000, 1, 1), datetime.date(2000, 1, 2),
             datetime.date(2000, 1, 3))
        )
        self.assertEqual(
            tuple(daterange(datetime.date(2000, 1, 1),
                            datetime.date(2000, 1, 7),
                            step=datetime.timedelta(days=2))),
            (datetime.date(2000, 1, 1), datetime.date(2000, 1, 3),
             datetime.date(2000, 1, 5))
        )
        return None


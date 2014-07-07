from django.contrib.auth.models import User, Group

from chores.models import ChoreSkeleton, Chore, Timecard, Signature
from profiles.models import UserProfile, GroupProfile

import datetime
import pytz

today = datetime.date.today()

dudley = Group(name='Dudley')
dudley.save()
dudley_profile = GroupProfile(group=dudley, short_name='Dudley Co-op',
                              short_description='3 Sac and 05.',
                              full_name='Harvard Co-operative House',
                              start_date=today+datetime.timedelta(days=-7),
                              cycle_length=14, release_buffer=4,
                              time_zone=pytz.UTC)
dudley_profile.save()

for name in ['Indy', 'Alex', 'Ruthe', 'Parker']:
    # TODO: set groups as well.
    name = name.lower()
    user = User.objects.create_user(name, '{nam}@dudley.coop'.format(nam=name),
                                    name)
    profile = UserProfile(user=user, coop=dudley, nickname=name,
                          first_name=name, middle_name='', last_name='Surname', 
                          email_address='{nam}@dudley.coop'.format(nam=name),
                          presence=14, share=1)
    profile.save()
    dudley.user_set.add(user)
dudley.save()

options = [
    {'short_description': 'Make dinner.', 'coop': dudley, 'point_value': 7,
     'short_name': 'Cook', 'start_time': datetime.time(15, 30), 'end_time':
     datetime.time(18, 30)},
    # {'short_description': 'Play a game to 21 with Joe.', 'coop': dudley,
     # 'point_value': 5, 'short_name': 'Ping Pong with Joe',
     # 'start_time': datetime.time(21, 15), 'end_time': datetime.time(22, 15)},
    {'short_description': 'Counters.', 'coop': dudley,
     'point_value': 4, 'short_name': 'KCU 1',
     'start_time': datetime.time(19, 30), 'end_time': datetime.time(20, 30)},
    {'short_description': 'Floors.', 'coop': dudley,
     'point_value': 4, 'short_name': 'KCU 2',
     'start_time': datetime.time(20, 30), 'end_time': datetime.time(21, 30)},
    {'short_description': 'Clean up after dinner.', 'coop': dudley,
     'point_value': 4, 'short_name': 'DRC',
     'start_time': datetime.time(19, 00), 'end_time': datetime.time(20, 00)},
    {'short_description': 'Prepare dining room for dinner.', 'coop': dudley,
     'point_value': 4, 'short_name': 'DRP',
     'start_time': datetime.time(17, 00), 'end_time': datetime.time(18, 00)},
    {'short_description': 'Sanitize stuff.', 'coop': dudley,
     'point_value': 4, 'short_name': 'MCU',
     'start_time': datetime.time(12, 00), 'end_time': datetime.time(13, 00)},
    {'short_description': 'Bake bread.', 'coop': dudley,
     'point_value': 7, 'short_name': 'Bread',
     'start_time': datetime.time(21, 00), 'end_time': datetime.time(23, 00)},
    {'short_description': 'Wash dishes.', 'coop': dudley,
     'point_value': 4, 'short_name': 'Dishes',
     'start_time': datetime.time(20, 00), 'end_time': datetime.time(21, 00)},
    {'short_description': 'Wash pots.', 'coop': dudley,
     'point_value': 9, 'short_name': 'Pots',
     'start_time': datetime.time(19, 00), 'end_time': datetime.time(22, 00)},
]

for option in options:
    ChoreSkeleton(**option).save()

for skeleton in ChoreSkeleton.objects.all():
    print('now doing {ske}'.format(ske=skeleton))
    for offset in range(-7, 7+1):
        print('offset: {off}'.format(off=offset))
        sig1 = Signature()
        sig1.save()
        sig2 = Signature()
        sig2.save()
        sig3 = Signature()
        sig3.save()
        date = today+datetime.timedelta(days=offset)
        chore = Chore(skeleton=skeleton, start_date=date, stop_date=date,
                      signed_up=sig1, signed_off=sig2,
                      voided=sig3)
        # TODO: could to do signing up, signing off, and voiding here.
        chore.save()

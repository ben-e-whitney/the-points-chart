from django.contrib.auth.models import User, Group

from chores.models import ChoreSkeleton, Chore, Timecard, Signature

import datetime

dudley = Group(name='Dudley')
dudley.save()

for name in ['Indy', 'Alex', 'Ruthe', 'Parker']:
    TODO: set groups as well.
    name = name.lower()
    User.objects.create_user(name, '{nam}@dudley.coop'.format(nam=name), name)

options = [
    {},
    {},
]

for option in options:
    ChoreSkeleton(**options).save()

today = datetime.date.today()
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

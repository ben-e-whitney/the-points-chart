from chores.models import ChoreSkeleton, Chore, Timecard, Signature

import datetime

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
        chore.save()

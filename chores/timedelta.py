import datetime

def in_interval(left, timedelta, right):
    '''
    Tests whether `timedelta` is contained in the half-open interval
    [`left` days, `right` days). If `left` is `None` then it is interpreted
    as ∞; similarly for `right`.
    '''
    if left is None:
        left = datetime.timedelta.min
    else:
        left = datetime.timedelta(left)
    if right is None:
        right = datetime.timedelta.max
    else:
        right = datetime.timedelta(right)
    return left <= timedelta < right

def pretty_print(timedelta):
    # TODO: this needs testing (including edge conditions).
    pretty_print = ''
    abs_td = abs(timedelta)
    if abs_td < datetime.timedelta(seconds=60):
        pretty_print += '{num} seconds'.format(num=abs_td.seconds)
    elif abs_td < datetime.timedelta(seconds=60**2):
    # For consistency I am not using rounding for these next two. See
    # <https://docs.python.org/3/library/datetime.html#timedelta-objects>.
        pretty_print += '{num} minutes'.format(num=abs_td.seconds//60)
    elif abs_td < datetime.timedelta(days=1):
        pretty_print += '{num} hours'.format(num=abs_td.seconds//60**2)
    else:
        pretty_print += '{num} days'.format(num=abs.td.days)
    # TODO: based on this, in the description of this function we should note
    # whether it expects 'now-then' or 'then-now'.
    if timedelta >= datetime.timedelta(0):
        pretty_print += ' ago'
    else:
        pretty_print += ' from now'
    return pretty_print

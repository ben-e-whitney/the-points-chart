import datetime
#TODO: look into the arrow package. <https://github.com/crsmithdev/arrow>.

def in_interval(left, timedelta, right, unit='days'):
    """
    Tests whether `timedelta` is contained in [`left` `unit`, `right` `unit`).

    If `left` is `None` then it is interpreted as ∞; similarly for `right`. The
    interval is always half-open, with the left boundary included.

    Arguments:
        left: left boundary of the interval (included).
        timedelta: timedelta whose inclusion in the interval is in question.
        right: right boundary of the interval (exluded).

    Keyword arguments:
        unit: unit of `left` and `right`.
    """

    if left is None:
        left = datetime.timedelta.min
    else:
        left = datetime.timedelta(**{unit: left})
    if right is None:
        right = datetime.timedelta.max
    else:
        right = datetime.timedelta(**{unit: right})
    return left <= timedelta < right

def pretty_print(timedelta):
    """
    Pretty print a timedelta.

    Positive timedeltas are understood as intervals since a time in the past.
    Negative timedeltas are understood as intervals until a time in the future.

    Arguments:
        timedelta: timedelta to be printed.
    """

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
        pretty_print += '{num} days'.format(num=abs_td.days)
    if timedelta >= datetime.timedelta(0):
        pretty_print += ' ago'
    else:
        pretty_print += ' from now'
    return pretty_print

def daterange(start, stop, step=datetime.timedelta(days=1), inclusive=False):
    """
    Yields datetimes in an interval.

    Arguments:
        start: lefthand endpoint of the interval (included).
        stop: righthand endpoint of the interval (excluded by default).

    Keyword arguments:
        step: amount by which consecutive datetimes should differ.
        inclusive: flag for whether to include `stop`.
    """

    if inclusive:
        stop += step
    date = start
    while date < stop:
        yield date
        date += step

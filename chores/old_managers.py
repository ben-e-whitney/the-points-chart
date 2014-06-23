#########################
# DELETE WHEN COMFORTABLE
#########################

class TimeWindowManager(models.Manager):

    '''
    Extends models.Manager, adding a few filtering methods for convenience.
    '''

    def in_window(self, coop, start_date, stop_date):
        '''
        Query the model database and return an iterator of Chore instances.

        Arguments:
            coop       -- Group whose chores we are interested in.
            start_date -- Beginning of time window.
            stop_date  -- End of the time window.

        Return an iterator yielding those chores which belong to the given
        `coop`, which start after or on `start_date`, and which end before or
        on `stop_date`. The results are ordered by starting date.
        '''

        # TODO: check whether you can first filter by skeleton__coop and sort,
        # and optionally later filter by start and stop dates (while preserving
        # the ordering).
        if start_date is None or stop_date is None:
            return self.filter(skeleton__coop=coop).order_by('start_date')
        else:
            return self.filter(
               skeleton__coop=coop,
               start_date__lte=start_date,
               stop_date__gte=stop_date,
            ).order_by('start_date')

    def signed(self, *args, signatures=None, users=itertools.repeat(None),
               desired_booleans=itertools.repeat(True)):
        # TODO: make other docstrings like this. See
        # <http://legacy.python.org/dev/peps/pep-0257/.
        '''
        Calls `in_window` with given arguments and filters based on Signatures.

        Keyword arguments:
            signatures       -- Iterable that yields attributes that
                `self.model` has as ForeignKeys to a Signature object.
            users            -- Iterable yielding a User (for when we care
                whether a given User has signed the corresponding Signature) or
                `None` (for when we only care whether any User has signed it).
            desired_booleans -- Iterable that yields Booleans we want the
                comparison involving the User and the Signature to return. See
                `acceptable` method for details.

        Returns an iterator of `self.model` object matches.
        Careful: if `signatures` is `['voided']`, `users` is `['None']`, and
        `desired_booleans` is ['True'], then chores which some User (*not*
        no/'None' User) has voided will be returned.
        '''

        def acceptable(chore):
            '''
            Judges whether chore satisfies criteria and returns a Boolean.

            Arguments:
                chore -- Chore (or similar) instance which is to be tested.

            `chore` is judged acceptable if each Signature object in
            `signatures` is signed off or signed off by the corresponding User.
            '''
            test_results = []
            for sig, user, desired_bool in zip(signatures, users,
                                               desired_booleans):
                if user is None:
                    result = bool(getattr(chore, sig))
                else:
                    result = getattr(chore, sig).who == user
                test_results.append(result)
            return all(test_results)

        # TODO: decide what this should return!
        return list(chore for chore in self.in_window(*args)
                    if acceptable(chore))

#############################################
# ALTERNATIONS MADE FOR THE STEWARDSHIP MODEL
#############################################

class TimeWindowManager(chore_TWM):

    '''
    Modification of `chore_TWM` to allow for different understanding of when a
    Stewardship falls inside a time window. See `in_window` documetation.
    '''

    # TODO: did we even change anything here? I do think we should -- just have
    # Chores fall on their start date, and do what we're doing here or whatever
    # for Stewardships. All cycles overlapped.
    def in_window(self, coop, start_date, stop_date):
        '''
        Overrides superclass method. Provides the same functionality.

        Arguments:
            coop       -- Group whose chores we are interested in.
            start_date -- Beginning of time window.
            stop_date  -- End of the time window.

        Changes from the superclass method are enclosed in asterisks.
        Return an iterator yielding those chores which belong to the given
        `coop`, which start before or on `stop_date`, and which end after or
        on `start_date`. The results are ordered by starting date.
        '''
        return self.filter(
           skeleton__coop=coop,
            start_date__lte=start_date,
            stop_date__gte=stop_date
        ).order_by('start_date')



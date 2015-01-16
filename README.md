Introduction
------------
the-points-chart is a Django project written to manage the chore systems of co-
operative houses. Its three primary concerns are

1. facilitating the bookkeeping necessary to fairly divide a shared workload
   into individual workloads
2. providing an interface used to sign up for chores
3. displaying all relevant information in a simple, easy-to-understand manner

An organization using the-points-chart will first categorize all tasks to be
done as either Chores (for recurring tasks that are tied to specific dates) or
Stewardships (for longer-running or ongoing tasks, like a Treasurer position).
Chores and Stewardships are assigned point values, and the work required of
each user in a chosen time interval (called a Cycle) is determined in terms of
these points. In the simplest case each user will be required to do the same
number of points, but there is also support for varied contribution levels,
absences, loans, etc. At the beginning of each Cycle, users sign themselves up
for Chores, and Stewardships are handled by users with special privileges. That
is, the-points-chart does not perform any sort of automatic scheduling.

If your organization's workload fits the model outlined above, the-points-chart
could save you a great deal of effort! If not, you are welcome to fork the code
to tweak behavior as desired, or even submit a pull request to the main
repository. Contributions are always welcome.

Authorship
----------
The primary author is Ben Whitney. Credit is also due to the many co-opers who
have used the chart and its predecessors, spotting bugs and suggesting
features, and, of course, to the many libraries and projects which
the-points-chart uses.

Licensing
---------
the-points-chart is released under the GPLv3, which is accessible
[here](http://www.gnu.org/copyleft/gpl.html).

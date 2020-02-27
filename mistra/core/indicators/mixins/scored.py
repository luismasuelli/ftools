from numpy import float_, NaN, isnan, vstack, ones
from ...utils.mappers.identity_mappers import IdentityMapper
from ...growing_arrays import GrowingArray


class ScoredMixin:
    """
    Adds capability to track its own score (a measure of performance)
      while running its lifecycle. In the end, the scoring is a float
      value in the range starting at 0 (shit) and ending at 1 (perfect),
      or NaN if a score is not available.

    Indicators implementing this trait/mixin will have its own growing
      array holding the scores for each time. Ideally, scoring involves
      several factors that evolve in time, but ultimately each score
      value does not depend on former values (unless a metric implies
      such behaviour).

    Implementors will have access to the `_scores` protected member to
      put a score for a given time, and a public `get_score` member to
      get the score for certain time. When putting a score, all the
      times before the score time will have a NaN value.
    """

    def __init__(self):
        self._scores = GrowingArray(float_, NaN, 3600, 1)

    def get_score(self, time):
        """
        Gets the score(s) from a specific time instant or slice.
        Negative indices are not supported and are silently clamped.
        Specifying a step != 1 is not supported and will raise an
          exception.

        Retrieving a single entry before the reference origin (0),
          will return NaN. For slices, no values will exist there,
          and nothing will be included from the past, as NaNs like
          it occurs in the single case.

        Retrieving a slice in the future will consist of the last
          score value available... repeated for the whole size of
          the slice.

        Retrieving a slice in the present will be no different.

        Retrieving a slice that is partially in the present and
          partially in the future will imply getting actual values
          first, and getting repeated values last.
        :param time: The time instant or slice to retrieve.
        :return:
        """
        size = len(self._scores)
        if isinstance(time, int):
            # Two distinct cases live here:
            # - NaN will be returned if there are no items
            #   or the requested time index is negative.
            # - A defined value will be returned for positive
            #   times, returning the last available scoring
            #   if the index is out of bounds.
            if size == 0 or time < 0:
                return NaN
            else:
                time = min(time, size - 1)
                return self._scores[time][:, 0]
        elif isinstance(time, slice):
            # First, slices will be preprocessed to only
            #   allow step=1 (or None), start < stop and
            #   both being integers (by default, start
            #   is 0 and stop is the array size). Both
            #   start and stop are clamped to disallow
            #   them to be negative values.
            start, stop, step = time.start, time.stop, time.step
            if not (step is None or step == 1):
                raise ValueError("Cannot slice the scores with a non-1 step")
            if start is None:
                start = 0
            if stop is None:
                stop = size
            start = max(0, start)
            stop = max(0, stop)
            if not (isinstance(start, int) and isinstance(stop, int)) or stop < start:
                raise ValueError("Slice's start and stop values must both be integer "
                                 "values and the start index must be <= the stop index")
            # The different scenarios will occur now:
            # - On size == 0, there is no available score.
            #   In this case an array of NaN values must
            #   be returned, with size == stop - start.
            # - On size <= start <= stop, an array will be
            #   returned but in this time it is filled with
            #   the last available score (the one at size
            #   - 1).
            # - On start <= stop <= size, an array of actual
            #   scores will be returned.
            # - The last case is start < size < stop. This
            #   case has both actual values and the filling
            #   with the last value, in two chunks:
            #   - [start:size]: actual values.
            #   - [size:stop]: fill values.
            if size == 0:
                return ones((stop - start,)) * NaN
            elif start >= size:
                return ones((stop - start,)) * self._scores[size - 1][:, 0]
            elif stop <= size:
                return self._scores[start:stop][:, 0]
            else:
                actual = self._scores[start:size][:, 0]
                repeated = ones((stop - size,)) * self._scores[size - 1][:, 0]
                return vstack((actual, repeated))
        else:
            raise TypeError("Invalid item type while getting the scores from a scored "
                            "object: only int or slices are supported")


class EvolvingMetricScoredMixin(ScoredMixin):
    """
    This particular scored mixin provides a new protected member that
      will allow us to report values and compute scores.

    This works by also having a chain of metrics that must be setup in
      the _setup method, including a computation of the "final" metric
      (which will be stored in the _scores array). Details are as follows:

      1. A "zero" metric will be registered, and will be the "performance".
         Values to that metric are added on each call to this method:

         self._report_performance(time, value).

      2. Chained metrics can be added on setup by invoking this method:

         def _setup(self):
             i1 = self.metric(0, lambda time, p0: ...)
             # i1 will be == 1
             i2 = self.metric(0, i1, lambda time, p0, p1: ...)
             # i2 will be == 2

         The signature of each function must include an amount of parameters
         matching the count of dependent metrics indices, and those must not
         refer any yet-non-existing metric. The time may either be a scalar
         or a vector, and numpy can help us in both cases. The result must
         have the appropriate type and shape, depending on what the time
         argument actually is.

      3. In the same setup, the final call (this means: no more calls can be
         done to the setup object) looks like this:

             self.result_metric(0, 1, 3, lambda time, p0, p1, p3: ...)

         Which means: to compute a result for the score for the given time(s),
         just involve the metrics 0, 1, and 3 and compute something from them.
    """

    def __init__(self):
        """
        Initializes this indicator by running a setup, validating it,
          and preparing to run according to the required metrics and
          scoring mechanism.
        """

        self._can_setup = False
        super().__init__()
        self._metrics = []
        self._next_metric_index = 1
        self._time_array = GrowingArray(int, NaN)
        self._metric_arrays = [
            GrowingArray(float, NaN)
        ]
        self._can_setup = True
        self._result_metric = self._make_metric(*self._setup())
        self._can_setup = False

    def _setup(self):
        """
        This method MUST be implemented by subclasses.

        It must consist of several calls to _add_metric, and
          return a pair of (dependencies, callback) with the
          same signature as in the _add_metric arguments.
          Such function will determine the "result metric",
          which ideally should return a value between 0 and
          1 for each execution.
        """

        raise NotImplemented

    def _make_metric(self, dependencies, implementation):
        """
        Given a pair of dependencies and implementation, it creates a
          function taking just an index, and returning the value of a
          single metric. The function passed as implementation must
          take arguments: one for the integer (time) index, one for
          the internal time array (the instant when the scoring is
          occurring), and an arbitrary list of arguments being the
          dependencies. Such... list... must be of the same length
          of the deps array.
        :param dependencies: Dependencies indices.
        :param implementation: Metric implementation.
        :return: A single-parameter function that performs the
          logic by taking an index and the required arrays from
          the metric arrays.
        """

        arrays = [IdentityMapper(self._metric_arrays[dep]) for dep in dependencies]
        return lambda index: implementation(index, self._time_array, *arrays)

    def _add_metric(self, dependencies, implementation):
        """
        Creates and adds an internal metric. The implementation function
          must expect two arguments (time index, time array) and an arbitrary
          list of parameters being the dependencies: its size must be equal
          to the size of the dependencies iterable.
        :param dependencies: Dependencies indices.
        :param implementation: Metric implementation.
        :return: The index of the just-created metric.
        """
        if not self._can_setup:
            raise RuntimeError("Metrics can only be setup inside a _setup() call")

        idx = self._next_metric_index
        if any(dep for dep in dependencies if dep < 0 or dep >= idx):
            raise IndexError("The metric being added references dependencies: {0}, "
                             "but this indicator only has dependencis from 0 to "
                             "{1}".format(dependencies, idx - 1))

        self._metric_arrays.append(GrowingArray(float, NaN))
        self._metrics.append(self._make_metric(dependencies, implementation))
        self._next_metric_index += 1
        return idx

    def _performance_report(self, time, value):
        """
        Reports the performance at certain time. This function must be
          invoked by children indicators that want to assess their own
          performance to others.
        :param time: The time to set a performance value for.
        :param value: The performance value to set.
        """

        # NaN values are not accepted in either time or value.
        if isnan(time) or isnan(value):
            raise ValueError("Time and value must be actual numbers - not NaN")

        # The size of the time array serves as the next index to insert
        #   in the growing arrays.
        size = len(self._time_array)

        # Prevents that performance data is added for time instants that
        #   are equal or lower to the last time already added.
        if size and self._time_array[size - 1][0] >= time:
            raise ValueError("Cannot tell the performance for a time index earlier "
                             "or equal to the already reported ones")

        # The first step is to fill the time value, and the performance
        #   value, in the respective arrays: the time array and the first
        #   metric array, in both cases at the position given at the size
        #   variable.
        self._time_array[size] = time
        self._metric_arrays[0][size] = value

        # Then, the metric implementations and the metric arrays are both
        #   iterated as a pair (except for metric array 0), and setting
        #   the current index (the same size variable) to the value returned
        #   by the respective metric(s).
        for impl, array in zip(self._metrics, self._metric_arrays[1:]):
            array[size] = impl(size)

        # Setting the result involves running the result metric... but in
        #   this case, not in a metric array but in the score array, using
        #   as index the time value instead of the size of the former arrays.
        # Middle -unfilled- values will be filled to the -formerly- last score,
        #   reflecting that "nothing changed in the meantime".
        result = self._result_metric(size)
        self._scores[time - 1] = self._scores[len(self._scores) - 1]
        self._scores[time] = result

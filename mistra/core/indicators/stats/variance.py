from numpy import empty, nan, hstack
from .. import Indicator
from .mean import MovingMean


class MovingVariance(Indicator):
    """
    Based on a moving mean indicator, this indicator tracks the variance and/or the standard deviation.
    Aside from moving mean, the following arguments may be specified:
    - Variance: Include the variance in the computation.
    - Std. Error: Include the standard error in the computation.
    - Unbiased: Whether to use the unbiased sample variance instead of the natural (biased) one.
    """

    def __init__(self, moving_mean, var=False, stderr=True, unbiased=True):
        if not isinstance(moving_mean, MovingMean):
            raise TypeError("For MovingVariance instances, the only allowed source indicator is a moving mean")
        if not (var or stderr):
            raise ValueError("At least one of the `var` or `stderr` flags must be specified")
        self._use_var = var
        self._use_stderr = stderr
        self._with_unbiased_correction = unbiased
        self._moving_mean = moving_mean
        Indicator.__init__(self, moving_mean)

    def _initial_width(self):
        """
        We may use both flags here, so the width may be 2.
        """

        if self._use_var and self._use_stderr:
            return 2
        return 1

    def _update(self, start, end):
        """
        Adds calculation of the variance and/or
        :param start: The start index to update.
        :param end: The end index to update.
        :return:
        """

        means = self._moving_mean[start:end]
        tail_runner = self._moving_mean.tail_runner
        tail_size = tail_runner.tail_size
        n = tail_size
        if self._with_unbiased_correction:
            n -= 1

        # This one HAS to be calculated.
        variance = empty((end - start, 1), dtype=float)
        for idx, chunk, incomplete in tail_runner.tail_iterate(start, end, self._moving_mean.parent):
            mean = means[idx - start]
            if incomplete:
                variance[idx - start] = nan
            else:
                variance[idx - start] = ((chunk - mean) ** 2).sum() / n

        # If we need the standard error, we also have to calculate this one.
        stderr = None
        if self._use_stderr:
            stderr = variance ** 0.5

        # Now we must assign the data appropriately.
        if self._use_var and self._use_stderr:
            self._data[start:end] = hstack([variance, stderr])
        elif self._use_var:
            self._data[start:end] = variance
        elif self._use_stderr:
            self._data[start:end] = stderr

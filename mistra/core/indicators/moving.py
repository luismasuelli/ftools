from numpy import NaN, array, nditer, empty, hstack

from . import Indicator
from ..sources import Source
from ..pricing import Candle


class MovingMean(Indicator):
    """
    Moving mean indicators are seldom used directly, but as dependencies for other indicators.
    They compute the moving mean of tail size = T, which is computed as the sample mean of the
      source elements in range [I-T+1:I+1].

    They can be used in the following frame types:
    - Integer source frames.
    - Float frames (other indicators) of width=1 (it is an error if they have different width).
    - Candle source frames, specifying which component to read (by default, the "end") price.

    The tail size must be an integer greater than 1.

    Finally, it can be specified to tell this indicator to store NaN instead of a moving mean if
      the index is lower than (tail size - 1).
    """

    def __init__(self, parent, tail_size, component='end', nan_on_short_tail=True):
        self._candle_component = None
        if isinstance(parent, Source):
            if parent.dtype == Candle:
                if component not in Candle.__slots__:
                    raise ValueError("For a candle-typed parent frame, the component argument must be among (start, "
                                     "end, min, max). By default, it will be 'end' (standing for the end price of the "
                                     "candle)")
                self._candle_component = component
        elif isinstance(parent, Indicator):
            if parent.width() != 1:
                raise ValueError("For an indicator parent frame, its width must be 1")
        if not isinstance(tail_size, int) or tail_size <= 1:
            raise ValueError("Tail size of a moving mean must be greater than 1")
        self._parent = parent
        self._tail_size = tail_size
        self._nan_on_short_tail = bool(nan_on_short_tail)
        Indicator.__init__(self, parent)

    def _update(self, start, end):
        """
        Updates the indices with the moving/tailed mean for -respectively- each index.
        :param start: The start index to update.
        :param end: The end index to update.
        """

        data = self._tail_slice(self._parent, start, end, self._tail_size)
        if self._candle_component:
            data = self._map(data, lambda c: getattr(c[0], self._candle_component), float)

        offset = data.shape[0] - end + start + 1
        for idx in range(0, end - start):
            tail_end = idx + offset
            tail_start = tail_end - self._tail_size
            if start + tail_start < 0 and self._nan_on_short_tail:
                self._data[start + idx] = NaN
            else:
                self._data[start + idx] = data[max(0, tail_start):tail_end].sum() / self._tail_size

    @property
    def parent(self):
        """
        The parent indicator.
        """

        return self._parent

    @property
    def candle_component(self):
        """
        The candle component, if the underlying source is of Candle type.
        """

        return self._candle_component

    @property
    def tail_size(self):
        """
        The tail size of this indicator.
        """

        return self._tail_size


class MovingVariance(Indicator):
    """
    Based on a moving mean indicator, this indicator tracks the variance and/or the standard deviation.
    Aside from moving mean, the following arguments may be specified:
    - Variance: Include the variance in the computation.
    - Std. Error: Include the standard error in the computation.
    - Unbiased: Whether use the unbiased sample variance instead of the natural (biased) one.
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

    def width(self):
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

        print("Calculating variance on indices:", start, end)

        means = self._moving_mean[start:end]

        print("Means shape:", means.shape)

        tail_size = self._moving_mean.tail_size
        values = self._tail_slice(self._moving_mean.parent, start, end, tail_size)
        ccmp = self._moving_mean.candle_component
        if self._moving_mean.candle_component:
            values = self._map(values, lambda c: getattr(c[0], ccmp), float)
        n = tail_size
        if self._with_unbiased_correction:
            n -= 1

        # This one HAS to be calculated.
        variance = empty((end - start, 1), dtype=float)

        offset = values.shape[0] - end + start + 1
        for idx in range(0, end - start):
            tail_end = idx + offset
            tail_start = tail_end - tail_size
            mean = means[idx]
            variance[idx] = ((values[max(0, tail_start):tail_end] - mean) ** 2).sum() / n

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

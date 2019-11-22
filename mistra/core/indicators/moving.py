from numpy import NaN, array, nditer

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

        data = self._parent[max(0, start + 1 - self._tail_size):end]
        if self._candle_component:
            data = self._map(data, lambda c: getattr(c[0], self._candle_component), float)

        for idx in range(0, end - start):
            tail_start = idx + 1 - self._tail_size
            tail_end = idx + 1
            if tail_start < 0 and self._nan_on_short_tail:
                self._data[tail_end - 1] = NaN
            else:
                self._data[tail_end - 1] = data[max(0, tail_start):tail_end].sum() / self._tail_size

    @property
    def tail_size(self):
        """
        The tail size of this indicator.
        """

        return self._tail_size


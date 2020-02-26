from numpy import NaN

from mistra.core.sources import Source
from mistra.core.indicators import Indicator
from mistra.core.indicators.tailed import TailedMixin


class MovingMean(TailedMixin, Indicator):
    """
    Moving mean indicators are seldom used directly, but as dependencies for other indicators.
    They compute the moving mean of tail size = T, which is computed as the sample mean of the
      source elements in range [I-T+1:I+1].

    They can be used in the following frame types:
    - Integer source frames.
    - Float frames (other indicators) of width=1 (it is an error if they have different width).

    The tail size must be an integer greater than 1.

    Finally, it can be specified to tell this indicator to store NaN instead of a moving mean if
      the index is lower than (tail size - 1).
    """

    def __init__(self, parent, tail_size, nan_on_short_tail=True):
        if isinstance(parent, Source):
            if parent.dtype != int and parent.dtype != float:
                raise TypeError("The parent source frame must be either int or float")
        elif isinstance(parent, Indicator):
            if parent.width() != 1:
                raise ValueError("For an indicator parent frame, its width must be 1")
        self._parent = parent
        self._nan_on_short_tail = bool(nan_on_short_tail)
        TailedMixin.__init__(self, tail_size)
        Indicator.__init__(self, parent)

    @property
    def parent(self):
        """
        The direct parent of this moving mean.
        """

        return self._parent

    def _update(self, start, end):
        """
        Updates the indices with the moving/tailed mean for -respectively- each index.
        :param start: The start index to update.
        :param end: The end index to update.
        """

        for idx, chunk, incomplete in self._tail_iterator(start, end, self._parent):
            if incomplete and self._nan_on_short_tail:
                self._data[idx] = NaN
            else:
                self._data[idx] = chunk.sum() / self._tail_size

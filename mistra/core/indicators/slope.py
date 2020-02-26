from numpy import NaN
from ..sources import Source
from .mixins.tailed import TailedMixin
from . import Indicator


class Slope(TailedMixin, Indicator):
    """
    Computes the nominal difference in prices between the current instant and the previous one.
    For the instant 0, computes the nominal difference in prices between that instance and the
      initial value. If the initial value is None, the nominal difference will be NaN.
    Since time intervals are constant, this differences are, in turn, the change slopes.
    """

    def __init__(self, parent):
        if isinstance(parent, Source):
            if isinstance(parent, Source):
                if not issubclass(parent.dtype, (int, float)):
                    raise TypeError("The parent source frame must be either int or float")
        elif isinstance(parent, Indicator):
            if parent.width() != 1:
                raise ValueError("For an indicator parent frame, its width must be 1")
        self._parent = parent
        TailedMixin.__init__(self, 2)
        Indicator.__init__(self, parent)

    def _update(self, start, end):
        """
        Updates the indices with the moving/tailed mean for -respectively- each index.
        :param start: The start index to update.
        :param end: The end index to update.
        """

        for idx, chunk, incomplete in self._tail_iterator(start, end, self._parent):
            if incomplete:
                if self._parent.initial is None:
                    self._data[idx] = NaN
                else:
                    self._data[idx] = chunk[0] - self._parent.initial
            else:
                self._data[idx] = chunk[1] - chunk[0]

    @property
    def parent(self):
        """
        The parent indicator.
        """

        return self._parent

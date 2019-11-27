from numpy import NaN

from ..sources import Source
from ..pricing import Candle
from . import Indicator


class Slope(Indicator):
    """
    Computes the nominal difference in prices between the current instant and the previous one.
    For the instant 0, computes the nominal difference in prices between that instance and the
      initial value. If the initial value is None, the nominal difference will be NaN.
    Since time intervals are constant, this differences are, in turn, the change slopes.
    """

    def __init__(self, parent, component='end'):
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
        self._parent = parent
        Indicator.__init__(self, parent)

    def _update(self, start, end):
        """
        Updates the indices with the moving/tailed mean for -respectively- each index.
        :param start: The start index to update.
        :param end: The end index to update.
        """

        data = self._tail_slice(self._parent, start, end, 2)
        if self._candle_component:
            data = self._map(data, lambda c: getattr(c[0], self._candle_component), float)

        for tail_start, tail_end, incomplete, idx in self._tail_iterate(data, start, end, 2):
            if incomplete:
                if self.source.initial is None:
                    self._data[idx] = NaN
                elif self._candle_component:
                    self._data[idx] = data[tail_end - 1] - getattr(self.source.initial, self._candle_component)
                else:
                    self._data[idx] = data[tail_end - 1] - self.source.initial
            else:
                self._data[idx] = data[tail_end - 1] - data[tail_start]

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

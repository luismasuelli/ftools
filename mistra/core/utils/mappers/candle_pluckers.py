from ...pricing import Candle
from .side_pluckers import SidePlucker
from . import map


class CandlePlucker:
    """
    A CandlePlucker expects a source having dtype == Candle,
      and its implementation of __getitem__ wraps the call
      to the wrapped source, and plucks the specified field
      from each candle. The source must actually be a
      SidePlucker instance.
    """

    def __init__(self, source, component='end'):
        if not isinstance(source, SidePlucker) or source.dtype != Candle:
            raise TypeError("The source must be a SidePlucker, and Candle-based")
        if component not in Candle.__slots__:
            raise ValueError("For a candle-typed source frame, the component argument must be among (start, "
                             "end, min, max). By default, it will be 'end' (standing for the end price of the "
                             "candle)")
        self._component = component
        self._source = source

    @property
    def component(self):
        return self._component

    def _pluck(self, element):
        return [getattr(element[0], self._component)]

    def __getitem__(self, item):
        return map(self._source, item, self._pluck, int)

    def __len__(self):
        return len(self._source)

    @property
    def initial(self):
        """
        Returns a pluck on the initial value of the underlying source.
        """

        if self._source.initial is None:
            return None
        else:
            return getattr(self._source.initial, self._component)

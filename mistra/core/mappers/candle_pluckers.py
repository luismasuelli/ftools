from ..pricing import Candle
from ..sources import Source
from . import map


class CandlePlucker:
    """
    A CandlePlucker expects a source having dtype == Candle,
      and its implementation of __getitem__ wraps the call
      to the wrapped source, and plucks the specified field
      from each candle.
    """

    def __init__(self, source, component='end'):
        if not isinstance(source, Source) or source.dtype != Candle:
            raise TypeError("The source must be a Source, and Candle-based")
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
        return [getattr(element, self._component)]

    def __getitem__(self, item):
        return map(self._source, item, self._pluck, int)

    @property
    def initial(self):
        """
        Returns a pluck on the initial value of the underlying source.
        """

        if self._source.initial is None:
            return None
        else:
            return getattr(self._source.initial, self._component)

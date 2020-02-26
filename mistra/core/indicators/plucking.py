from ..sources import Source
from ..pricing import Candle
from ..indicators import Indicator


class Plucking(Indicator):
    """
    Plucking indicators just pluck a specific component
      from a candle - they are linked to candle-type
      sources. By default, they pluck the "end" component
      of a candle.
    """

    def __init__(self, parent, component='end'):
        if not isinstance(parent, Source) or parent.dtype != Candle:
            raise TypeError("The parent must be a Source, and Candle-based.")
        if component not in Candle.__slots__:
            raise ValueError("For a candle-typed parent frame, the component argument must be among (start, "
                             "end, min, max). By default, it will be 'end' (standing for the end price of the "
                             "candle)")
        self._component = component
        super().__init__(parent)

    @property
    def component(self):
        """
        The component being plucked.
        """

        return self._component

    def _update(self, start, end):
        """
        Fills the data by plucking a candle's component.
        :param start: The start index.
        :param end: The end index.
        """

        self._data[start:end] = self._map(self.source[start:end], lambda c: getattr(c[0], self._component), float)

    def width(self):
        return 1

    @property
    def initial(self):
        """
        Returns a pluck on the initial value of the underlying source.
        """

        if self.source.initial is None:
            return None
        else:
            return getattr(self.source.initial, self._component)

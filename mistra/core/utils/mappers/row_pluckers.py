from ...indicators import Indicator
from . import map


class RowPlucker:
    """
    A RowPlucker expects an indicator (which will have dtype
      == float) and a row that must belong to range [0, width),
      and its implementation of __getitem__ wraps the call
      to the wrapped source, and plucks the specified column
      from each row.
    """

    def __init__(self, indicator, row=0):
        if not isinstance(indicator, Indicator) or 0 >= indicator.width():
            raise TypeError("The indicator must be an Indicator, with a well-setup width")
        if not (isinstance(row, int) and 0 <= row < indicator.width()):
            raise ValueError("For an indicator frame, the row argument must be in the range of "
                             "{0 .. width-1} and must be an integer")
        self._row = row
        self._indicator = indicator

    @property
    def row(self):
        return self._row

    def _pluck(self, element):
        return [element[self._row]]

    def __getitem__(self, item):
        return map(self._indicator, item, self._pluck, float)

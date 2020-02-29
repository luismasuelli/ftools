from numpy import NaN
from ..sources import Source
from ..utils.tail_runners import TailRunner
from ..utils.mappers.smart_pluckers import smart_plucker
from . import Indicator


class Slope(Indicator):
    """
    Computes the nominal difference in prices between the current instant and the previous one.
    For the instant 0, computes the nominal difference in prices between that instance and the
      initial value. If the initial value is None, the nominal difference will be NaN.
    Since time intervals are constant, this differences are, in turn, the change slopes.

    Two additional arguments: component and row. They are required depending on the given parent.
    """

    def __init__(self, parent, side=Source.ASK, component='end', row=0):
        self._parent = smart_plucker(parent, side, component, row)
        self._tail_runner = TailRunner(2)
        Indicator.__init__(self, parent)

    def _update(self, start, end):
        """
        Updates the indices with the moving/tailed mean for -respectively- each index.
        :param start: The start index to update.
        :param end: The end index to update.
        """

        for idx, chunk, incomplete in self._tail_runner.tail_iterate(start, end, self._parent):
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

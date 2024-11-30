from numpy import nan
from ...sources import Source
from ...utils.mappers.smart_pluckers import smart_plucker
from ...utils.tail_runners import TailRunner
from .. import Indicator


class MovingMean(Indicator):
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

    Two additional arguments: component and row. They are required depending on the given parent.
    """

    def __init__(self, parent, tail_size, nan_on_short_tail=True, side=Source.ASK, component='end', row=0):
        self._parent = smart_plucker(parent, side, component, row)
        self._nan_on_short_tail = bool(nan_on_short_tail)
        self._tail_runner = TailRunner(tail_size)
        Indicator.__init__(self, parent)

    @property
    def tail_runner(self):
        """
        The internal tail runner.
        """

        return self._tail_runner

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

        for idx, chunk, incomplete in self._tail_runner.tail_iterate(start, end, self._parent):
            if incomplete and self._nan_on_short_tail:
                self._data[idx] = nan
            else:
                self._data[idx] = chunk.sum() / self._tail_runner.tail_size

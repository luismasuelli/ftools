from numpy import uint64, array, empty, NaN
from datetime import datetime, timedelta
from mistra.core.sources import Source
from mistra.core.intervals import Interval
from mistra.core.pricing import StandardizedPrice, Candle
from mistra.core.indicators import Indicator


class Identity(Indicator):

    def __init__(self, source):
        self._bc_source = source
        Indicator.__init__(self, source)

    def width(self):
        return 1

    def _update(self, start, end):
        print("Updating indices %d:%d in identity" % (start, end))
        self._data[start:end] = self._bc_source[start:end]


class MovingMean(Indicator):

    def __init__(self, source, tail):
        self._bc_source = source
        self._tail = min(tail, 2)
        Indicator.__init__(self, source)

    def width(self):
        return 1

    def _update(self, start, end):
        print("Updating indices %d:%d in moving mean[%d]" % (start, end, self._tail))
        for idx in range(start, end):
            tail_start = idx+1-self._tail
            tail_end = idx+1
            if tail_start < 0:
                self._data[tail_end - 1] = NaN
            else:
                self._data[tail_end - 1] = self._bc_source[tail_start:tail_end].sum() / self._tail


class Merger(Indicator):

    def __init__(self, mmean, identity):
        self._bc_mmean = mmean
        self._bc_identity = identity
        Indicator.__init__(self, mmean, identity)

    def width(self):
        return 2

    def _update(self, start, end):
        print("Updating indices %d:%d in merger" % (start, end))
        data = empty((end - start, self.width()), dtype=float)
        data[:, 0] = self._bc_identity[start:end][:, 0]
        data[:, 1] = self._bc_mmean[start:end][:, 0]
        print(data.shape)
        self._data[start:end] = data


today = Interval.DAY.round(datetime.now())


source = Source(StandardizedPrice, today, Interval.HOUR, initial=1)
source.push(array((2, 4, 6, 8, 10, 12, 14), dtype=uint64), index=4)
source.push(array((16, 18, 20, 22), dtype=uint64))
print(source[:])


identity = Identity(source)
movmean2 = MovingMean(source, 2)
merger = Merger(movmean2, identity)

print("identity:", identity[:])
print("moving mean:", movmean2[:])
print("merger", merger[:])

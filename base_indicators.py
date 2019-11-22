from numpy import array, empty
from datetime import datetime
from mistra.core.sources import Source
from mistra.core.intervals import Interval
from mistra.core.pricing import Candle
from mistra.core.indicators import Indicator
from mistra.core.indicators.moving import MovingMean, MovingVariance


class Identity(Indicator):

    def __init__(self, source):
        self._bc_source = source
        Indicator.__init__(self, source)

    def width(self):
        return 1

    def _update(self, start, end):
        self._data[start:end] = self._map(self._bc_source[start:end], function=lambda row: row[0].start, dtype=float)


class Merger(Indicator):

    def __init__(self, mmean, identity):
        self._bc_mmean = mmean
        self._bc_identity = identity
        Indicator.__init__(self, mmean, identity)

    def width(self):
        return 2

    def _update(self, start, end):
        data = empty((end - start, self.width()), dtype=float)
        data[:, 0] = self._bc_identity[start:end][:, 0]
        data[:, 1] = self._bc_mmean[start:end][:, 0]
        print(data.shape)
        self._data[start:end] = data


today = Interval.DAY.round(datetime.now())


source = Source(Candle, today, Interval.HOUR, initial=Candle.constant(0))
source.push(array(list(Candle.constant(v) for v in (2, 4, 6, 8, 10, 12, 14)), dtype=Candle), index=4)
source.push(array(list(Candle.constant(v) for v in (16, 18, 20, 22)), dtype=Candle))
print(source[:])


identity = Identity(source)
movmean2 = MovingMean(source, 2)
merger = Merger(movmean2, identity)
variance = MovingVariance(movmean2, var=True, stderr=True, unbiased=True)

source.push(array(list(Candle.constant(v) for v in (100, 200, 300, 400, 500)), dtype=Candle))

print("identity:", identity[:])
print("moving mean:", movmean2[:])
print("merger", merger[:])
print("varnace", variance[:])
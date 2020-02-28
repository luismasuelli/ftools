from numpy import array, empty
from datetime import datetime
from mistra.core.sources import Source
from mistra.core.intervals import Interval
from mistra.core.pricing import Candle
from mistra.core.indicators import Indicator
from mistra.core.indicators.stats.mean import MovingMean
from mistra.core.indicators.stats.variance import MovingVariance
from mistra.core.indicators.slope import Slope


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


source = Source(Candle, today, Interval.HOUR, initial_bid=Candle.constant(0), initial_ask=Candle.constant(1))
source.push(array(list((Candle.constant(v-1), Candle.constant(v)) for v in (2, 4, 6, 8, 10, 12, 14)), dtype=Candle),
            index=4)
source.push(array(list((Candle.constant(v), Candle.constant(v+1)) for v in (16, 18, 20, 22)), dtype=Candle))
print(source[:])


movmean2 = MovingMean(source, 2)
variance = MovingVariance(movmean2, var=True, stderr=True, unbiased=True)
slope = Slope(source)

source.push(array(list((Candle.constant(v), Candle.constant(v+2)) for v in (100, 200, 300, 400, 500)), dtype=Candle))

print("moving mean:", movmean2[:])
print("variance", variance[:])
print("slope", slope[:])

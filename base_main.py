from numpy import uint64, array
from datetime import datetime, timedelta
from mistra.core.sources import Source
from mistra.core.intervals import Interval
from mistra.core.pricing import StandardizedPrice, Candle


today = Interval.DAY.round(datetime.now())


source = Source(StandardizedPrice, today, Interval.HOUR, initial=1)
source.push(array((2, 4, 6, 8, 10, 12, 14), dtype=uint64), index=today + timedelta(hours=4))
source.push(array((16, 18, 20, 22), dtype=uint64))
print(source[:])


linked = Source(Candle, today - timedelta(hours=8), Interval.HOUR2, initial=Candle.constant(0))
linked.link(source)
print(linked[:])
linked.push(array(tuple(Candle.constant(v) for v in (30, 31, 32, 33)), dtype=Candle), 0)
print(linked[:])


# Re-set old data
source.push(array((100, 110, 120, 130), dtype=uint64), 0)
print(source[:])
print(linked[:])


# Disconnect the linked frame
linked.unlink()


# Update market data in the source frame with 3 elements.
source.push(array((400, 410, 420), dtype=uint64))


# relink the former frame.
linked.link(source)


# Print the linked marked data.
print(linked[:])

from numpy import uint64, array
from datetime import datetime, timedelta
from mistra.core.sources import Source
from mistra.core.intervals import Interval
from mistra.core.pricing import StandardizedPrice, Candle


today = Interval.DAY.round(datetime.now())


source = Source(StandardizedPrice, today, Interval.HOUR, initial_bid=1, initial_ask=2)
source.push(array(((2, 2), (4, 4), (6, 6), (8, 9), (10, 11), (12, 13), (14, 15)), dtype=uint64), index=today + timedelta(hours=4))
source.push(array(((16, 16), (18, 19), (20, 21), (22, 23)), dtype=uint64))
print(source[today:])


linked = Source(Candle, today - timedelta(hours=8), Interval.HOUR2, initial_bid=Candle.constant(0), initial_ask=Candle.constant(1))
linked.link(source)
print(linked[:])
print(linked[4])
print(linked[today])
linked.push(array(tuple((Candle.constant(v), Candle.constant(v+1)) for v in (30, 31, 32, 33)), dtype=Candle), 0)
print(linked[:])


# Re-set old data
source.push(array(((100, 101), (110, 111), (120, 121), (130, 131)), dtype=uint64), 0)
print(source[:])
print(linked[:])


# Disconnect the linked frame
linked.unlink()


# Update market data in the source frame with 3 elements.
source.push(array(((400, 401), (410, 411), (420, 421)), dtype=uint64))


# relink the former frame.
linked.link(source)


# Print the linked marked data.
print(linked[:])

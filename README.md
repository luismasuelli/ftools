MISTRA (Market InSights and TRading Algorithms)
===============================================

This is essentially a time series manager suitable for markets (stocks, ForEx).

This base package provides features related to the lifecycle of time series, which involve:
  - Parent time series.
  - Linked (digest) time series.
  - Indicators (which can be connected to either parent or linked time series).

1 - Parent Time Series
----------------------

These are the series you will create and feed with data. This is the main work point of
any market interaction (i.e. watching a market evolution, like EUR/USD, involves creating
one of these parent frames and feeding it with historical or real-time data).

*Note: while time series can be fed with data, automated providers are not included in this package.*

To create your main market view you should first instantiate a `Source`:

```
from datetime import datetime, timedelta
from mistra.core.sources import Source
from mistra.core.intervals import Interval
from mistra.core.pricing import StandardizedPrice, Candle

# The date this data belongs to - It is optional, but good practice, to
#   round it for the day it belongs to.
yesterday = Interval.DAY.round(datetime.now() - timedelta(days=1))

# The actual market time serie for the selected date (yesterday).
main_eur_usd = Source(StandardizedPrice, yesterday, Interval.SECOND)
```

Once you create your `main_eur_usd` parent time series, you will do either of the following:

  - Add data to this time series.
  - Link children time series to this one.

In the order you desire (data will be appropriately refreshed for the children time series anyway if you add them later).

2 - Adding data to the Parent Time Series
-----------------------------------------

Following the same example, you will add data with the following methods:

1. Scalar data (with simple index).

```
# Push at immediate next position.
price = (6000000, 6000002)
main_eur_usd.push(price)

# Push at specified position, even if AFTER the immediate next.
# It may cause interpolation of existing->new data!
# This index is an example: It may mean 2 hours after source's date
#   when the chosen interval size per slot is 1 second.
price = (6000000, 6000002)
index = 7200
main_eur_usd.push(price, index)

# We can also use a datetime index as well. If the interval is 1
#   second, this example would be equivalent to the former.
price = (6000000, 6000002)
index = yesterday + timedelta(hours=2)
main_eur_usd.push(price, index)
```

2. Array data (with slice index).

```
from numpy import array

# For all these examples, let the prices be:
prices = array([[5000000, 5000002], [5000001, 5000003], [5000002, 5000004], [5000001, 5000003], [4999999, 5000001]], dtype=StandardizedPrice)

# Push at immediate next position.
main_eur_usd.push(prices)

# Push at specified position (with all the same considerations stated for scalar values).
main_eur_usd.push(prices, 7200)

# Push at specified datetime position (with all the same considerations stated for scalar values).
main_eur_usd.push(prices, yesterday + timedelta(hours=2))
```

Following these notes:

1. If the source's type is `StandardizedPrice`, you will use scalar integer values, or
   1-dimensional numpy arrays of integer values.
2. If the source's type is `Candle`, you will use scalar `Candle` values, or 1-dimensional
   numpy arrays of `Candle` values.

And you can query the data as well, with the following considerations:

1. You can use non-negative integer indices.
2. You can use datetime indices that are after the source frame's start date.
3. You can omit any of the indices when using slices.
4. You can mix integer and timestamp indices in slices.
5. You cannot use a step different to `None` or `1`.

Examples:

```
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

main_eur_usd[0]

main_eur_usd[today]

main_eur_usd[:]

main_eur_usd[0:]

main_eur_usd[:today+timedelta(hours=5)]
```

The result will be a numpy array when a slice is provided, and a scalar array (integer or
  `Candle`, depending on the underlying type) when a single index is provided.

3 - Linking digest frames
-------------------------

Digest frames are useful when a broader view is needed (a broader view implies reduced
information using wider intervals - e.g. watching digests in hours instead of in seconds).

Digests are regular source frames that can be linked to other source frames. Usually, one
main source will be needed per market (e.g. one for EUR/USD), and several digests will be
linked to them. Say, for example:

  - The main source is at second-level intervals.
  - One digest will be at 1-minute-level intervals.
  - Another digest at 5-minute-level intervals.
  - Another digest at 15-minute-level intervals.
  - Another digest at 1-hour-level intervals.

Adding data to the main source will automagically reflect (in an appropriate way) in the
digest frames that are connected to it.

To connect a digest frame to a source frame, you can proceed like this:

```
digest_1m = Source(Candle, yesterday, Interval.MINUTE)
digest_1m.link(main_eur_usd)

# Then you work on the `main_eur_usd` as you want...

# Then you can query the values in the digest, the exact same way you'd in the main source.

digest_1m[0]

digest_1m[today]

digest_1m[:]

digest_1m[0:]

digest_1m[:today+timedelta(hours=5)]
```

With the following considerations:

1. After the call to `link(source)`, the digest will initialize itself by refreshing the data for the first time.
2. Digests can only connect to a source frame having a date greater than or equal the digest's date.
3. Also, the frame's date must be divisible by the digest's interval as well (e.g. you cannot connect a
   1-hour-level digest to a 1-second-level interval frame starting at 5:30 of some day, since it is not
   divisible by 1 hour).
4. It is allowed to set the digest data using `push` as in the source data, but it is usually useful for datetimes
   / indices that are lower than the linked source's data.
5. `unlink()` can be called to stop linking the source. It will work as another regular source and, if another link
   is requested and done, it will perform -again- the same refresh in `1.`.

3 - Indicators
--------------

Indicators are derived frames that can be connected to source frames, and never unlinked (but instead permanently
disposed).

Like digests, they will refresh automatically and can stop/resume their refresh activity. Unlike digests, they will
belong to the exact time space (interval size and start date) of the source they are created for, and also the data
they produce/bring is made up via a particular algorithm each indicator implements (e.g. moving mean, moving
variance).

While digests produce a broader view of the market evolution, indicators produce a specific derived data that may
not be quite evident at first sight.

Indicators may nest, and in fact they will most times. The deeper nesting level, the more complex the information
generated by the indicator.

To create an indicator, you can go like this:

```
from mistra.core.indicators.moving import MovingMean, MovingVariance

moving_mean = MovingMean(main_eur_usd, 20)
moving_variance = MovingVariance(moving_mean)
```

Indicators follow an acyclic hierarchy (for they reference their dependencies on creation), hence all the events
  will follow that hierarchy all the way down.

After creation, Not only the dependencies are set, but also the first data update will trigger.

To dispose an indicator, you will go like this:

```
moving_variance.dispose()
```

***Note**: A disposed indicator may be considered destroyed, and will also trigger disposal in other indicators that
  depend on this one.*

And to query an indicator, you will go like you normally do in sources:

```
moving_variance[0]

moving_variance[today]

moving_variance[:]

moving_variance[0:]

moving_variance[:today+timedelta(hours=5)]
```

They will work just like retrieving data from sources/digests.

4 - More features
-----------------

There are still more desired features like plotting, several implementations for indicators, and data providers.

However they will NOT be implemented in **this** package, but in other -plugin-like- packages for MISTRA.

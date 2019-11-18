from numpy import ndarray, uint64
from .timelapses import Timelapse
from .events import Event
from .pricing import StandardizedPrice, Candle
from .growing_arrays import GrowingArray


class Source(Timelapse):
    """
    Source frames are the origin of the data. Internally, they are organized as a sequence of indexed prices
      or candles (depending on the required type: standardized price or candle).

    A type, an initial timestamp (e.g. day of activity) and an interval type is needed for the source frame
      know its context of work. After that, data may be added (either to the next available index or a given
      index that must be at least greater to the next one) and, if discontinuous, it will cause a kind of
      padding or interpolation in the frame data.

    When data is added, it will refresh two types of related (derived) frames:
      - Digests of the current frame.
      - Indicators of this frame.
    """

    def __init__(self, dtype, stamp, interval, initial=None):
        """
        Creates a source frame with certain type, initial timestamp, an interval and an initial value.
        :param dtype: Either standardized price or candle.
        :param stamp: The initial time stamp. It will correspond to the sequence index 0.
        :param interval: The required interval.
        :param initial: The initial value for this frame. Usually being dragged from previous period.
          It must NOT be null if we don't plan to provide data for index 0.
        """

        if not interval.allowed_as_source():
            raise ValueError('The given interval is not allowed as source frame interval: %s' % interval)
        if dtype not in (StandardizedPrice, Candle):
            raise ValueError('The source frame type must be either pricing.Candle or pricing.StandardizedPrice')
        if initial is not None:
            if dtype == StandardizedPrice and not isinstance(initial, int):
                raise TypeError("For pricing.StandardizedPrice type, the initial value must be integer")
            elif dtype == Candle and not isinstance(initial, Candle):
                raise TypeError("For pricing.Candle type, the initial value must be a candle instance")
        Timelapse.__init__(self, dtype, interval, 3600, 1)
        self._timestamp = stamp
        self._initial = initial
        self._on_refresh_digests = Event()
        self._on_refresh_indicators = Event()
        self._linked_to = None

    def _get_timestamp(self):
        """
        Implements the timestamp property by returning the owned timestamp.
        """

        return self._timestamp

    @property
    def on_refresh_indicators(self):
        """
        Indicators will connect to this event to refresh themselves when more data is added.
        """

        return self._on_refresh_indicators

    @property
    def on_refresh_digests(self):
        """
        Digests will connect to this event to refresh themselves when more data is added.
        """

        return self._on_refresh_digests

    def _interpolate(self, previous_value, start, end, next_value):
        """
        Causes an interpolation of data in certain index range, and considering
          boundary values.
        :param previous_value: The left-side value.
        :param start: The start index.
        :param end: The end index (not included).
        :param next_value: The right-side value.
        """

        # We'll state a new reference system where the previous value is at 0,
        #   and the next value is at distance, and we'll fill values from 1 to
        #   distance - 1.
        distance = end - start + 1
        # Iterating from index 1 to index {distance-1}, not including it.
        if isinstance(previous_value, int):
            delta = float(next_value - previous_value)/distance
            for index in range(0, distance - 1):
                self._data[start + index] = int(delta * (index + 1) + previous_value)
        elif isinstance(previous_value, Candle):
            delta_start = float(next_value.start - previous_value.start) / distance
            delta_end = float(next_value.end - previous_value.end) / distance
            delta_max = float(next_value.max - previous_value.max) / distance
            delta_min = float(next_value.min - previous_value.min) / distance
            for index in range(0, distance - 1):
                self._data[start + index] = Candle(
                    start=int(delta_start * (index + 1) + previous_value.start),
                    end=int(delta_end * (index + 1) + previous_value.end),
                    min=int(delta_min * (index + 1) + previous_value.min),
                    max=int(delta_max * (index + 1) + previous_value.max)
                )

    def _interpolate_and_put(self, push_index, push_data):
        """
        It will try an interpolation -if needed- of the data, considering the last index, the
          initial value of this frame, and the first element of the data to push.

        In the end, the new data (including the interpolated, if the case) will start at index
          self._last_index+1 and will end at index (push_index + {push_data.size or 1}), not
          including that index.
        :param push_index: The index the data is being pushed at.
        :param push_data: The data being pushed.
        """

        length = len(self)
        left_side = self._initial if length == -1 else self._data[length]
        needs_interpolation = push_index - 1 > length
        is_ndarray = isinstance(push_data, ndarray)
        if needs_interpolation:
            if length == -1 and left_side is None:
                raise RuntimeError("Cannot add data: interpolation is needed for the required index "
                                   "to push the data into, but an initial value was never set for "
                                   "this frame")
            # Performs the interpolation.
            right_side = push_data[0] if is_ndarray else push_data
            self._interpolate(left_side, length + 1, push_index, right_side)
        # Performs the insertion.
        if is_ndarray:
            self._data[push_index:push_index+push_data.size] = push_data[:]
        else:
            self._data[push_index] = push_data

    def link(self, digest):
        """
        Links this frame to another digest, so data can be updated from it into this frame's data.
        It is an error to link to a digest with a different interval size or a LOWER date: frames can
          only link to digests with a greater date (and back-fill positions in previous time stamps).
        Linking to a digest will automatically unlink from the previous digest, if any.
        :param digest: The digest to link to.
        """

        self.unlink()
        if digest.timestamp < self._timestamp:
            raise ValueError("The date of the digest attempted to link to is lower than this frame's date")
        if digest.interval < self.interval:
            raise ValueError("The digest to link to must have the same interval of this frame")
        self._linked_to = digest.on_refresh_linked_sources
        self._linked_to.register(self._on_linked_refresh)
        # Force the first refresh.
        self._on_linked_refresh(digest.timestamp, 0, len(digest))

    def unlink(self):
        """
        Unlinks this frame from its currently linked digest.
        :return:
        """

        self._linked_to.unregister(self._on_linked_refresh)
        self._linked_to = None

    def _on_linked_refresh(self, digest, start, end):
        """
        Handles an update from the linked digest considering start date and boundaries.
        It is guaranteed that boundaries will be in the same scale of this frame, but
          it has also be taken into account the start date to use as offset for the
          start and end indices.
        :param digest: The linked digest.
        :param start: The start index, in the digest, of the updated data.
        :param end: The end index (not including), in the digest, of the updated data.
        """

        base_index = self.index_for(digest.timestamp)
        self.push(digest[start:end], base_index + start)

    def push(self, data, index=None):
        """
        Adds data, either scalar of the expected type, or a data chunk of the expected type.
        Always, at given index.

        :param data: The data to add.
        :param index: The index to add the data at. By default, the next index. It is allowed
          to update old data, but think it twice: it MAY trigger an update of old data, not account
          for actual data re-interpolation, and cascade the changes forward in unpredictable ways,
          which may involve SEVERAL QUITE COSTLY COMPUTATIONS!!.
        :return:
        """

        if index is None:
            index = len(self)
        if index < 0:
            raise IndexError("Index to push data into cannot be negative")
        self._interpolate_and_put(index, data)
        # Arrays have length in their shape, while other elements have size=1.
        end = index + (1 if not isinstance(data, ndarray) else data.shape[0])
        self._on_refresh_digests.trigger(index, end)
        self._on_refresh_indicators.trigger(index, end)

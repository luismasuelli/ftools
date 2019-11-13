from datetime import timedelta
from numpy import array, ndarray, uint64
from .events import Event
from .intervals import Interval
from .pricing import StandardizedPrice, Candle
from .timelapses import Timelapse


DAY_SIZE = int(Interval.DAY)


class SourceFrame(Timelapse):
    """
    Source frames are the origin of the data. Internally, they are organized as a sequence of indexed prices
      or candles (depending on the required type: standardized price or candle).

    A type, an initial timestamp (e.g. day of activity) and an interval type is needed for the source frame
      know its context of work. After that, data may be added (either to the next available index or a given
      index that must be at least greater to the next one) and, if discontinuous, it will cause a kind of
      padding or interpolation in the frame data (this implies: data must be added IN STRICT ORDER to work
      properly), up to the index 86399. Also, the views this source frame will support.

    When data is added, it will refresh two types of related (derived) frames:
      - Views of the current frame.
      - Indicators tied to this frame.
        - Inside of each indicator, its views (which are of, strictly, the same size of the views
          in THIS frame).
    """

    def __init__(self, type, stamp, interval, initial=None):
        """
        Creates a source frame with certain type, initial timestamp, an interval and an initial value.
        :param type: Either standardized price or candle.
        :param stamp: The initial time stamp. It will correspond to the sequence index 0.
        :param interval: The required interval.
        :param initial: The initial value for this frame. Usually being dragged from previous period.
          It must NOT be null if we don't plan to provide data for index 0.
        """

        if not interval.allowed_as_source():
            raise ValueError('The given interval is not allowed as source frame interval: %s' % interval)
        if type not in (StandardizedPrice, Candle):
            raise ValueError('The source frame type must be either pricing.Candle or pricing.StandardizedPrice')
        if initial is not None:
            if type == StandardizedPrice and not isinstance(initial, int):
                raise TypeError("For pricing.StandardizedPrice type, the initial value must be integer")
            elif type == Candle and not isinstance(initial, Candle):
                raise TypeError("For pricing.Candle type, the initial value must be a candle instance")
        Timelapse.__init__(self, interval)
        self._type = type
        self._timestamp = stamp
        self._last_index = -1
        self._initial = initial
        # TODO some day, break this limitation and create some sort of "growing data" instead of
        # TODO   using a fixed size frame spanning at most 1 day.
        size = DAY_SIZE/int(interval)
        self._data = array((size,), dtype=type)
        self._on_refresh_views = Event()
        self._on_refresh_indicators = Event()

    @property
    def type(self):
        """
        The type of element this frame works with. Either StandardizedPrice (int) or Candle (Candle).
        """

        return self._type

    def _get_timestamp(self):
        """
        Implements the timestamp property by returning the owned timestamp.
        """

        return self._timestamp

    @property
    def on_refresh_views(self):
        """
        Views will connect to this event to refresh themselves when more data is added.
        """

        return self._on_refresh_views

    @property
    def on_refresh_indicators(self):
        """
        Indicators will connect to this event to refresh themselves when more data is added.
        """

        return self._on_refresh_indicators

    def __getitem__(self, item):
        """
        Gets values from the underlying array.
        :param item: The item (index or slice) to use to get the data from the underlying array.
        :return:
        """

        return self._data[item]

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
                self._data[start + index] = delta*(index + 1) + previous_value
        elif isinstance(previous_value, Candle):
            delta_start = float(next_value.start - previous_value.start)/distance
            delta_end = float(next_value.end - previous_value.end)/distance
            delta_max = float(next_value.max - previous_value.max)/distance
            delta_min = float(next_value.min - previous_value.min)/distance
            for index in range(0, distance - 1):
                self._data[start + index] = Candle(
                    start=delta_start*(index + 1) + previous_value.start,
                    end=delta_end*(index + 1) + previous_value.end,
                    min=delta_min*(index + 1) + previous_value.min,
                    max=delta_max*(index + 1) + previous_value.max
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

        left_side = self._initial if self._last_index == -1 else self._data[self._last_index]
        needs_interpolation = push_index - 1 > self._last_index
        is_ndarray = isinstance(push_data, ndarray)
        if needs_interpolation:
            if self._last_index == -1 and left_side is None:
                raise RuntimeError("Cannot add data: interpolation is needed for the required index "
                                   "to push the data into, but an initial value was never set for "
                                   "this frame")
            # Performs the interpolation.
            right_side = push_data[0] if is_ndarray else push_data
            self._interpolate(left_side, self._last_index + 1, push_index, right_side)
        # Performs the insertion.
        if is_ndarray:
            self._data[push_index:push_index+push_data.size] = push_data[:]
        else:
            self._data[push_index] = push_data

    def push(self, data, index=None):
        """
        Adds data, either scalar of the expected type, or a data chunk of the expected type.
        Always, at given index.

        If the frame is full, or would fill and overflow given the data or chunk, an exception
          will be raised. The maximum frame size is 86400/{interval size}.
        :param data: The data to add.
        :param index: The index to add the data at. By default, the next index. It must always
          be greater than the current last index.
        :return:
        """

        if index is None:
            index = self._last_index + 1
        if index < 0:
            raise IndexError("Index to push data into cannot be negative")
        if index <= self._last_index:
            raise IndexError("Specified index is already used: %d" % index)
        is_ndarray = isinstance(data, ndarray)
        is_int_ndarray = is_ndarray and data.dtype == uint64
        is_obj_ndarray = is_ndarray and data.dtype == object
        is_int = isinstance(data, int)
        is_obj = isinstance(data, Candle)
        if is_ndarray and len(data.shape) != 1:
            raise TypeError("Only 1-dimensional numpy arrays are allowed")
        if self._type == Candle:
            if not (is_obj or is_obj_ndarray):
                raise TypeError("Data being added must be of Candle (scalar/numpy array) type")
        elif self._type == StandardizedPrice:
            if not (is_int or is_int_ndarray):
                raise TypeError("Data being added must be of int or uint64 numpy array type")
        length = 1 if not is_ndarray else data.size
        if index + length >= 86400 / int(self._interval):
            raise RuntimeError("This frame is full - no further data can be added")
        self._interpolate_and_put(index, data)
        end = index + length
        self._last_index = end - 1
        self._on_refresh_views.trigger(end)
        self._on_refresh_indicators.trigger(end)

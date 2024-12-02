from datetime import timedelta, date, datetime
from .domains import DiscreteTimeDomain
from .events import Event
from .growing_arrays import GrowingArray


class Timelapse(DiscreteTimeDomain):
    """
    Timelapse is an abstract class allowing us to handle common utilities regarding
      datetimes in frames, digests, and indicators. They will also give yp the data,
      in the end, but will not handle it: they will give the feature to their
      subclasses.
    """

    def __init__(self, dtype, fill_value, chunk_size, width):
        """
        Creates the timelapse.
        :param dtype: The data type.
        :param chunk_size: The chunk size for the underlying growing array.
        :param width: The width of each data item.
        :param fill_value: The value to fill the empty spaces in the data when initialized.
        """

        self._on_refresh_indicators = Event()
        self._data = GrowingArray(dtype, fill_value, chunk_size, width)

    @property
    def on_refresh_indicators(self):
        """
        This event will be triggered on data change so the indicators can update.
        """

        return self._on_refresh_indicators

    @property
    def width(self):
        """
        Returns the width of this timelapse, based on
        what's set in the underlying array's width.
        :return: The width.
        """

        return self._data.width

    def __getitem__(self, item):
        """
        Gets values from the underlying array. It is also allowed to use timestamps instead of
          indices: they will be converted (by truncation/alignment) to the appropriate indices.
        :param item: The item (index or slice) to use to get the data from the underlying array.
        :return:
        """

        if isinstance(item, (date, datetime)):
            item = self.index_for(item)
        elif isinstance(item, slice):
            start = item.start
            stop = item.stop
            if isinstance(start, (date, datetime)):
                start = self.index_for(start)
            if isinstance(stop, (date, datetime)):
                stop = self.index_for(stop)
            item = slice(start, stop, item.step)
        return self._data[item][:]

    def __len__(self):
        return len(self._data)

    @property
    def dtype(self):
        """
        The underlying type of this source frame.
        """

        return self._data.dtype

    def has_item(self, item):
        """
        Tells whether this time slice has populated the given index or stamp, or not yet.
        :param item: The index or stamp to check.
        :return: Whether it has been populated or not.
        """

        if isinstance(item, (date, datetime)):
            item = self.index_for(item)
        return item < len(self._data)

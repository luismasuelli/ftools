from datetime import timedelta, date, datetime
from .growing_arrays import GrowingArray


class Timelapse:
    """
    Timelapse is an abstract class allowing us to handle common utilities regarding
      datetimes in frames, digests, and indicators. They will also give yp the data,
      in the end, but will not handle it: they will give the feature to their
      subclasses.
    """

    def __init__(self, dtype, fill_value, interval, chunk_size, width):
        """
        Creates the timelapse.
        :param dtype: The data type.
        :param interval: The interval.
        :param chunk_size: The chunk size for the underlying growing array.
        :param width: The width of each data item.
        :param fill_value: The value to fill the empty spaces in the data when initialized.
        """

        self._interval = interval
        self._data = GrowingArray(dtype, fill_value, chunk_size, width)

    def stamp_for(self, index):
        return self._get_timestamp() + timedelta(seconds=index * int(self._interval))

    def index_for(self, stamp):
        return int((stamp - self._get_timestamp()).total_seconds()) // int(self._interval)

    @property
    def interval(self):
        """
        The interval size for this source. Digests must use BIGGER intervals in order to be able to
          connect to this source.
        """

        return self._interval

    def _get_timestamp(self):
        """
        Abstract method that returns the reference timestamp to use.
        """
        raise NotImplemented

    @property
    def timestamp(self):
        return self._get_timestamp()

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

    def has_item(self, item):
        """
        Tells whether this time slice has populated the given index or stamp, or not yet.
        :param item: The index or stamp to check.
        :return: Whether it has been populated or not.
        """

        if isinstance(item, (date, datetime)):
            item = self.index_for(item)
        return item < len(self._data)

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
        result = self._data[item][:]
        if isinstance(item, slice):
            # Flattening this array to be 1-dimensional, since now it is
            #   of shape (size, 1).
            result.shape = (result.shape[0],)
        else:
            # It is am array with just 1 element! Just extract it.
            result = result[0]
        return result

    def __len__(self):
        return len(self._data)

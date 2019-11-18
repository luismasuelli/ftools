from numpy import uint32
from .intervals import Interval
from .pricing import Candle
from .timelapses import Timelapse
from .growing_arrays import GrowingArray


class Digest(Timelapse):
    """
    Digests can be connected to source frames to summarize their data: they have an interval size which
      must be BIGGER to the interval size in the referenced source.
    """

    def __init__(self, source, interval):
        if source is None:
            raise ValueError("The source for the digest must not be None")
        if not interval.allowed_as_digest(source.interval):
            raise ValueError("The chosen digest interval size must be bigger to the source's interval size")
        Timelapse.__init__(self, interval)
        self._source = source
        self._data = GrowingArray(uint32, 240, 1)
        self._last_source_index = -1
        self._source.on_refresh_digests.register(self._on_refresh)
        self._attached = True
        self._relative_bin_size = int(interval)/int(source.interval)

    @property
    def source(self):
        """
        The source this digest is attached to.
        """

        return self._source

    def _get_timestamp(self):
        """
        Implements the timestamp by returning the source's timestamp.
        """

        return self._source.timestamp

    @property
    def attached(self):
        """
        Tells whether this digest is still attached and working, or not.
        """

        return self._attached

    def detach(self):
        """
        Detaches this digest from the source. This digest will be useless since will
          not update its data anymore.
        """

        self._source.on_refresh_digests.unregister(self._on_refresh)
        self._attached = False

    def __getitem__(self, item):
        """
        Gets values from the underlying array.
        :param item: The item (index or slice) to use to get the data from the underlying array.
        :return:
        """

        return self._data[item]

    def _on_refresh(self, end):
        """
        Updates the current digest given its data. It will give the last index the digest will
          have to process until (perhaps the digest has former data already parsed, and so
          it will have to collect less data). Several source indices falling in the same
          digest index will involve a candle merge.
        :param end: The source-scaled end index the digest will have to refresh until (and not
          including).
        """

        start = self._last_source_index + 1
        for source_index in range(start, end):
            digest_index = source_index // self._relative_bin_size
            candle = self._data[digest_index]
            source_element = self._source[source_index]
            if candle is None:
                if isinstance(source_element, Candle):
                    candle = source_element
                elif isinstance(source_element, int):
                    candle = Candle(source_element, source_element, source_element, source_element)
            else:
                candle = candle.merge(source_element)
            self._data[digest_index] = candle
        self._last_source_index = max(self._last_source_index, end - 1)

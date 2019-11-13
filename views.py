from numpy import array
from .intervals import Interval
from .pricing import Candle
from .timelapses import Timelapse


DAY_SIZE = int(Interval.DAY)


class View(Timelapse):
    """
    Views can be connected to either sources or indicators. There is no difference, as they will
      be digests of both, correspondingly. Views have an interval size which must be BIGGER to
      the interval size in the indicator or the source.
    """

    def __init__(self, source, interval):
        if source is None:
            raise ValueError("The source for the view must not be None")
        if not interval.allowed_as_view(source.interval):
            raise ValueError("The chosen view interval size must be bigger to the source's interval size")
        Timelapse.__init__(self, interval)
        self._source = source
        # TODO continue here the same issue in the Source
        size = DAY_SIZE/int(interval)
        self._data = array((size,), dtype=Candle)
        self._last_source_index = -1
        self._source.on_refresh_views.register(self._on_refresh)
        self._attached = True
        self._relative_bin_size = int(interval)/int(source.interval)

    @property
    def source(self):
        """
        The source this view is attached to.
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
        Tells whether this view is still attached and working, or not.
        """

        return self._attached

    def detach(self):
        """
        Detaches this view from the source. This view will be useless since will
          not update its data anymore.
        """

        self._source.on_refresh_views.unregister(self._on_refresh)
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
        Updates the current view given its data. It will give the last index the view will
          have to process until (perhaps the view has former data already parsed, and so
          it will have to collect less data). Several source indices falling in the same
          view index will involve a candle merge.
        :param end: The source-scaled end index the view will have to refresh until (and not
          including).
        """

        start = self._last_source_index+1
        for source_index in range(start, end):
            view_index = source_index // self._relative_bin_size
            candle = self._data[view_index]
            source_element = self._source[source_index]
            if candle is None:
                if isinstance(source_element, Candle):
                    candle = source_element
                elif isinstance(source_element, int):
                    candle = Candle(source_element, source_element, source_element, source_element)
            else:
                candle = candle.merge(source_element)
            self._data[view_index] = candle
        self._last_source_index = end

from .events import Event


class IndicatorBroadcaster:
    """
    It can register indicators and also provide a way to notify them regarding changes in
      data. In the same way, provides a mean to return its own data.
    """

    def __init__(self, interval, timestamp):
        self._on_refresh_indicators = Event()
        self._interval = interval
        self._timestamp = timestamp

    @property
    def on_refresh_indicators(self):
        """
        This event will be triggered on data change so the indicators can update.
        """

        return self._on_refresh_indicators

    @property
    def interval(self):
        """
        The interval for this indicator broadcaster.
        """

        return self._interval

    @property
    def timestamp(self):
        """
        Gets the starting timestamp for this broadcaster
        :return:
        """

        return self._timestamp

    def __getitem__(self, item):
        """
        Gets underlying data from this broadcaster.
        """

        raise NotImplementedError


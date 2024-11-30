from .events import Event


class IndicatorBroadcaster:
    """
    It can register indicators and also provide a way to notify them regarding changes in
      data. In the same way, provides a mean to return its own data.
    """

    def __init__(self, source):
        self._on_refresh_indicators = Event()
        self._source = source

    @property
    def on_refresh_indicators(self):
        """
        This event will be triggered on data change so the indicators can update.
        """

        return self._on_refresh_indicators

    @property
    def source(self):
        """
        The source this broadcaster ultimately get the data from.
        """

        return self._source

    def __getitem__(self, item):
        """
        Gets underlying data from this broadcaster.
        """

        raise NotImplementedError

    def __len__(self):
        """
        Returns the length of this indicator (which will be: the length
        of the underlying source and be always sure it is properly up
        to-date with it).
        """

        return len(self._source)

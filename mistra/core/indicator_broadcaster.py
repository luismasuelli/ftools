from .events import Event


class IndicatorBroadcaster:
    """
    It can register indicators and also provide a way to notify them regarding changes in
      data.
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

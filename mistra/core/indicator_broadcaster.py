from .events import Event


class IndicatorBroadcaster:
    """
    It can register indicators and also provide a way to notify them regarding changes in
      data.
    """

    def __init__(self):
        self._on_refresh_indicators = Event()

    @property
    def on_refresh_indicators(self):
        """
        This event will be triggered on data change so the indicators can update.
        """

        return self._on_refresh_indicators

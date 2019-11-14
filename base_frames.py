from .timelapses import Timelapse
from .events import Event


class BaseFrame(Timelapse):
    """
    Base frames are frames with the highest granularity. Sources and indicators are,
      actually, base frames. Views connect to them.
    """

    def __init__(self, interval):
        Timelapse.__init__(self, interval)
        self._on_refresh_views = Event()

    @property
    def on_refresh_views(self):
        """
        Views will connect to this event to refresh themselves when more data is added.
        """

        return self._on_refresh_views


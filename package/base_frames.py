from .events import Event
from .timelapses import Timelapse


class BaseFrame(Timelapse):
    """
    Base frames are frames with the highest granularity. Digests connect to them.
    """

    def __init__(self, interval):
        Timelapse.__init__(self, interval)
        self._on_refresh_digests = Event()

    @property
    def on_refresh_digests(self):
        """
        Digests will connect to this event to refresh themselves when more data is added.
        """

        return self._on_refresh_digests


from datetime import timedelta


class Timelapse:
    """
    Timelapse is an abstract class allowing us to handle common utilities regarding
      datetimes in frames, views, and indicators.
    """

    def __init__(self, interval):
        self._interval = interval

    def stamp_for(self, index):
        return self._get_timestamp() + timedelta(seconds=index * int(self._interval))

    def index_for(self, stamp):
        return (stamp - self._get_timestamp()).total_seconds() / int(self._interval)

    @property
    def interval(self):
        """
        The interval size for this source. Views must use BIGGER intervals in order to be able to
          connect to this source, for views are digests.
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

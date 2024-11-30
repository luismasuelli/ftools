from datetime import timedelta


class DiscreteTimeDomain:
    """
    A discrete time domain is just a reference to a starting point,
    followed by a length and conditioned by a "bin size" (in terms
    of a time interval), and then having the "next" point. Both
    the start and next points are datetime objects, and the next
    point is the immediately next time point to arrive, typically.
    """

    def stamp_for(self, index):
        return self._get_timestamp() + timedelta(seconds=index * int(self._get_interval()))

    def index_for(self, stamp):
        return int((stamp - self._get_timestamp()).total_seconds()) // int(self._get_interval())

    @property
    def interval(self):
        """
        The interval size for this source. Digests must use BIGGER intervals in order to be able to
          connect to this source.
        """

        return self._get_interval()

    def _get_interval(self):
        """
        Abstract method that returns the interval to use.
        """

        raise NotImplemented

    @property
    def timestamp(self):
        """
        Stands for the initial timestamp (the one corresponding to the
        zero index) of this timelapse.
        :return: The initial timestamp.
        """

        return self._get_timestamp()

    def _get_timestamp(self):
        """
        Abstract method that returns the reference timestamp to use.
        """

        raise NotImplemented

    @property
    def next_timestamp(self):
        """
        Stands for the post-final timestamp / next timestamp (the one
        corresponding to the next stamp to use when adding new data).
        :return: The post-final / next timestamp.
        """

        return self.stamp_for(len(self))

    def __len__(self):
        """
        Computes the length of the current time space. This length
        can evolve: increment with new samples.
        """

        raise NotImplemented

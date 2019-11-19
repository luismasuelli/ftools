from enum import IntEnum


class Interval(IntEnum):
    """
    These values can be used as intervals for source (original data) or digested data.
    They can also constrain/truncate a timestamp to be relevant for the interval being considered.
    """

    SECOND = 1
    MINUTE = 60*SECOND
    MINUTE5 = 5*MINUTE
    MINUTE10 = 10*MINUTE
    MINUTE15 = 15*MINUTE
    MINUTE20 = 20*MINUTE
    MINUTE30 = 30*MINUTE
    HOUR = 60*MINUTE
    HOUR2 = 2*HOUR
    HOUR3 = 3*HOUR
    HOUR4 = 4*HOUR
    HOUR6 = 6*HOUR
    HOUR8 = 8*HOUR
    HOUR12 = 12*HOUR
    DAY = 24*HOUR

    def allowed_as_source(self):
        """
        Tells whether this interval can be used in a source frame.
        """

        return self != Interval.DAY

    def allowed_as_digest(self, for_source_interval=SECOND):
        """
        Tells whether this interval can be used in a digest frame given a related source frame size.
        Aside from being allowed, this interval size must be GREATER than the given, optional, one.
        :param for_source_interval: The source frame size to compare.
        """

        iself = int(self)
        ifor = int(for_source_interval)
        return iself % ifor == 0 and iself > ifor

    def round(self, stamp):
        """
        Rounds a timestamp down to the relevant interval. E.g. the MINUTE interval will round down,
          removing the seconds (setting them to 0), while the MINUTE5 will, also, round down the minutes
          in chunks of 5.
        :param stamp: The stamp to round down.
        :return: The rounded stamp.
        """
        if self == self.SECOND:
            return stamp.replace(microsecond=0)
        elif self == self.MINUTE:
            return stamp.replace(microsecond=0, second=0)
        elif self == self.MINUTE5:
            return stamp.replace(microsecond=0, second=0, minute=(stamp.minute // 5) * 5)
        elif self == self.MINUTE10:
            return stamp.replace(microsecond=0, second=0, minute=(stamp.minute // 10) * 10)
        elif self == self.MINUTE15:
            return stamp.replace(microsecond=0, second=0, minute=(stamp.minute // 15) * 15)
        elif self == self.MINUTE20:
            return stamp.replace(microsecond=0, second=0, minute=(stamp.minute // 20) * 20)
        elif self == self.MINUTE30:
            return stamp.replace(microsecond=0, second=0, minute=(stamp.minute // 30) * 30)
        elif self == self.HOUR:
            return stamp.replace(microsecond=0, second=0, minute=0)
        elif self == self.HOUR2:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=(stamp.hour // 2) * 2)
        elif self == self.HOUR3:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=(stamp.hour // 3) * 3)
        elif self == self.HOUR4:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=(stamp.hour // 4) * 4)
        elif self == self.HOUR6:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=(stamp.hour // 6) * 6)
        elif self == self.HOUR8:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=(stamp.hour // 8) * 8)
        elif self == self.HOUR12:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=(stamp.hour // 12) * 12)
        elif self == self.DAY:
            return stamp.replace(microsecond=0, second=0, minute=0, hour=0)
        else:
            raise AssertionError("An unexpected interval type (perhaps there's a bug or pending work here) tried "
                                 "to round a timestamp")

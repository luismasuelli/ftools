from ...sources import Source


class SidePlucker:
    """
    A side plucker plucks one of the sides of a source flow: the bid or the ask.
    For this to work, the argument for a side plucker must be a source, with any
      type: its type will not care at all.
    """

    BID = 0
    ASK = 1

    pluck_index = None

    def __init__(self, source, side):
        if not isinstance(source, Source):
            raise TypeError("The source must be a Source")
        if side not in (Source.BID, Source.ASK):
            raise ValueError("The side choice must be either Source.BID / 0, or Source.ASK / 1")
        self._source = source
        self._side = side

    @property
    def side(self):
        return self._side

    @property
    def dtype(self):
        return self._source.dtype

    @property
    def initial(self):
        return self._source.initial[self._side]

    def __getitem__(self, item):
        return self._source[item, self._side]

    def __len__(self):
        return len(self._source)


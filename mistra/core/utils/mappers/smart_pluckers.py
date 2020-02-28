from ...sources import Source
from ...indicators import Indicator
from ...pricing import Candle
from .side_pluckers import SidePlucker
from .candle_pluckers import CandlePlucker
from .row_pluckers import RowPlucker


def smart_plucker(source, side=Source.ASK, component='end', row=0):
    """
    Depending on the source's type, it will be
      smart enough to instantiate a plucker, or
      return the source as-is. In the end, it
      returns a mean to get a width=1 source.
    Also, if it is a source, it will use a specific
      side (and not both) to fetch.
    :param source: The source to wrap.
    :param side: The flow side to pick.
    :param component: The component to pluck.
      Used if the source is Candle-type.
    :param row: The row to pluck.
      Used if the source is an indicator.
    :return: A width=1 mapper.
    """

    if isinstance(source, Source):
        if source.dtype == Candle:
            return CandlePlucker(SidePlucker(source, side), component)
        elif source.dtype == int:
            return SidePlucker(source, side)
        else:
            raise TypeError("The source has an unexpected dtype")
    elif isinstance(source, Indicator):
        return RowPlucker(source, row)
    else:
        raise TypeError("The source must be either a Source or an Indicator")

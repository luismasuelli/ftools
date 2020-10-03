"""
Providers load or scrap market data to make back-testing or real-time
  population of market data into sources.

Actually, these are two different provider types, and can be compatible
  with certain intervals and data types, while others have different
  compatibilities.
"""

from mistra.core.sources import Source
from .pricing import Candle


class BackTestingProvider:
    """
    Performs a huge bulked data load from a specific historic data source.

    Each back-testing provider will support or allow their own set of intervals,
      and either be via internet or by reading a local file, which may cause an
      heterogeneous range of errors, which are wrapped into a BackTestingProvider.Error
      exception.

    Right now, it is only allowed to create Candle-typed sources, and not price sources
      of StandardizedPrice type.

    To create a provider class, just inherit this class and override `_execute(self)`
      returning a tuple of two results: the buy price source and the sale price source.

    To invoke a provider, just call it like a function:

        source = my_provider_instance()
    """

    class Error(Exception):
        pass

    def _execute(self):
        """
        This abstract method must be implemented to execute the actual provision
          and also ensure to return a source as result, providing both bid/ask
          prices in it..
        """

        raise NotImplemented

    def _merge(self, stamp, buy_price, sale_price, source):
        """
        Merges two prices in certain timestamp into the current source's respective
          candles. If the stamp is not yet populated with the price for that source,
          it makes a constant candle out of it. On the other hand, it merges the input
          price into the current candle.
        :param stamp: The associated timestamp of the prices.
        :param buy_price: The buy price to add or merge, which is standardized (i.e.
          scaled to convert the decimal point to an integer).
        :param sale_price: The sale price to add or merge, which is standardized (i.e.
          scaled to convert the decimal point to an integer).
        :param source: The source to add or merge that price.
        """

        if source.has_item(stamp):
            buy_price = source[stamp][Source.BID].merge(buy_price)
            sale_price = source[stamp][Source.ASK].merge(sale_price)
            source.push((buy_price, sale_price), stamp)
        else:
            source.push((Candle.constant(buy_price),
                         Candle.constant(sale_price)))

    def __call__(self):
        """
        Executes the actual bulk load. Any exception is wrapped into a BackTestingProvider.Error.
        :return: The new source.
        """

        try:
            return self._execute()
        except Exception as e:
            raise self.Error(e)

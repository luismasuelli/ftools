"""
Providers load or scrap market data to make back-testing or real-time
  population of market data into sources.

Actually, these are two different provider types, and can be compatible
  with certain intervals and data types, while others have different
  compatibilities.
"""


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

      buy_price_source, sell_price_source = my_provider_instance()
    """

    class Error(Exception):
        pass

    def _execute(self):
        """
        This abstract method must be implemented to execute the actual provision
          and also ensure to return two sources (buy price, sale price) in a tuple.
        :return: A tuple of two sources: (buy price, sale price).
        """

        raise NotImplemented

    def __call__(self):
        """
        Executes the actual bulk load. Any exception is wrapped into a BackTestingProvider.Error.
        :return: Two sources in a tuple: (buy price evolution, sale price evolution).
        """

        try:
            return self._execute()
        except Exception as e:
            raise self.Error(e)


class RealTimeProvider:
    """
    Real-time providers do not create sources but link to them, to continuously feed them.

    Currently, it is only supported that they work with candles, and not standardized prices.
    """

    def __init__(self):
        self._linked_buy_price_sources = set()
        self._linked_sale_price_sources = set()

    def _merge(self, stamp, price, source):
        """
        Merges a price in certain timestamp into the current source's respective candle.
          If the stamp is not yet populated with the price for that source, it makes a
          constant candle out of it. On the other hand, it merges the input price into
          the current candle.
        :param stamp: The associated timestamp of the prices.
        :param price: The price to add or merge, which is standardized (i.e. scaled to
          convert the decimal point to an integer).
        :param source: The source to add or merge that price.
        """

        if source.has_item(stamp):
            source.push(source[stamp].merge(price), stamp)
        else:
            source.push(Candle.constant(price))

    def _feed(self, stamp, buy, sale):
        """
        Given a time instant and their buy/sale prices, feeds the linked buy/sale sources
          accordingly.

        This is an internal method that MUST be called by implementors, but it is up to them
          to define where, when and how to call it.

        :param stamp: The associated timestamp of the prices.
        :param buy: The buy price, which is standardized (i.e. scaled to convert the decimal
          point to an integer).
        :param sale: The sale price, which is standardized like the buy price.
        """

        for source in self._linked_buy_price_sources:
            self._merge(stamp, buy, source)

        for source in self._linked_sale_price_sources:
            self._merge(stamp, sale, source)

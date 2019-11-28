"""
Indicators are a different monster. They handle a growing array of width N, where
  N is a different constant, depending on the indicator class. While row indices
  refer different instants, column indices refer different features the indicators
  may have. All the cells in this (dynamic)xN array will be of float type, and each
  indicator will have to deal with that to the appropriate extent.

Indicators will depend, alternatively, on (or: "be created with"):
  - A source frame (directly).
  - Another indicator(s) (directly) and the underlying frame (indirectly). All the
      indicators MUST have the same frame (directly or not).

Indicators cannot unlink that dependency [although they should be able to halt (stop
  updating), resume, and dispose (halt forever, and destroy the underlying data in
  an unrecoverable way)] and pick another one, since it gives the appropriate way of
  refreshing the data on other -dependent- indicators. They are tied to the indicators
  or source they are created from, and those indicators or source will forward data
  updates to them.

When an indicator is disposed, all the dependent indicators will also dispose.

A quite complex network of indicators may be used. For example: One single moving mean
  of the last 20 time slices / candles / instants can feed a moving variance of the last
  20 time slices / candles / instants (which contains both the variance and the stderr),
  which in turn can feed 5 different Bollinger Bands indicators.
"""
from datetime import date, datetime

from numpy import float_, NaN, array
from ..growing_arrays import GrowingArray
from ..indicator_broadcaster import IndicatorBroadcaster


class Indicator(IndicatorBroadcaster):
    """
    Base class for indicators. Indicators depend ultimately on broadcasters, but they have
      to have the same source. Inheritors should have a way to distinguish each provided
      dependency.
    """

    def __init__(self, *broadcasters):
        broadcasters = set(broadcasters)
        sources = set(broadcaster.source for broadcaster in broadcasters)
        if len(sources) != 1:
            raise ValueError("Indicators must receive at least a source and/or several other indicators, and "
                             "all the given input arguments must have the same source")
        IndicatorBroadcaster.__init__(self, sources.pop())
        self._max_requested_start = {broadcaster: 0 for broadcaster in broadcasters}
        self._max_requested_end = {broadcaster: 0 for broadcaster in broadcasters}
        self._disposed = False
        self._data = GrowingArray(float_, NaN, 3600, self.width())
        # Trigger first refresh
        for broadcaster in broadcasters:
            broadcaster.on_refresh_indicators.register(self._on_dependency_update)
        for broadcaster in broadcasters:
            self._on_dependency_update(broadcaster, 0, len(broadcaster))

    def width(self):
        """
        The width of this indicator's data.
        """

        return 1

    def disposed(self):
        """
        Tells whether the current indicator is disposed (i.e. it will not work anymore, and data cannot
          be retrieved from it).
        """

        return self._disposed

    def __getitem__(self, item):
        """
        Returns data from this indicator.
        :param item: The index or slice to retrieve data at.
        """

        if self._disposed:
            raise RuntimeError("Cannot retrieve indicator data because it is disposed")
        elif isinstance(item, (date, datetime)):
            item = self.source.index_for(item)
        elif isinstance(item, slice):
            start = item.start
            stop = item.stop
            if isinstance(start, (date, datetime)):
                start = self.source.index_for(start)
            if isinstance(stop, (date, datetime)):
                stop = self.source.index_for(stop)
            item = slice(start, stop, item.step)
        return self._data[item]

    def __len__(self):
        return len(self._data)

    def dispose(self):
        """
        Clears this indicator from its dependency and bradcasts this call towards dependent
          indicators.
        """

        if not self._disposed:
            self._disposed = True
            self._data = None
            self._broadcasters_read = None
            for broadcaster in self._broadcasters_read.keys():
                broadcaster.on_refresh_indicators.unregister(self._on_dependency_update)
            for callback, receiver in self._on_refresh_indicators:
                receiver.dispose()

    def _on_dependency_update(self, dependency, start, end):
        """
        Processes a data update event. Such event will first be triggered from the source
        :param dependency: The dependency being updated.
        :param start: The internal index of the dependency being updated.
        :param end:
        :return:
        """

        # The maximum requested read for a dependency is the topmost read index
        #   up to now. Among every maximum requested index, we will get the minimum.
        self._max_requested_end[dependency] = max(end, self._max_requested_end[dependency])
        minimum_requested_end = min(r for r in self._max_requested_end.values())
        # Now we must also consider the minimum of this last index, and the currently requested end.
        current_end = min(minimum_requested_end, end)

        # For the start index (which will be <= than the end index), we still
        #   collect the maximums between the last read and the current start for,
        #   and still get the minimum among them.
        self._max_requested_start[dependency] = max(start, self._max_requested_start[dependency])
        minimum_requested_start = min(r for r in self._max_requested_start.values())
        # Then we also compare, and get minimum of, the minimum requested start, and the current start.
        current_start = min(minimum_requested_start, start)

        # Once we have these indices, we can invoke to refresh the data.
        self._update(current_start, current_end)

        # Then trigger to refresh the indicators.
        self._on_refresh_indicators.trigger(self, current_start, current_end)

    def _update(self, start, end):
        """
        Performs the update. This method must be implemented, account for all the needed dependencies, and also
          accounting for the fact that data may be NaN!
        :param start: The start index being refreshed.
        :param end: The end index (not included) being refreshed.
        """

        raise NotImplemented

    def _map(self, data, function, dtype):
        """
        Maps a bi-dimensional array into another bi-dimensional array, perhaps of different
          width, given a mapping function and its dtype.
        :param data: The data to use as map source.
        :param function: The function used to map the data.
        :param dtype: The dtype for the new array.
        :return: A new array with the mapped data.
        """

        mapped = list(function(data[idx, :]) for idx in range(data.shape[0]))
        return array(mapped, dtype=dtype)

    def _tail_slice(self, data, start, end, tail_size):
        """
        Creates a slice of the given data (which will most often a source of the
          same scale/interval of the current indicator, and often a dependency)
          by considering the start and end indices (which are often provided in
          the context of data update) and a positive integer tail size.

        The slice is created according to the following criteria:
          - First, the end index is usually as-is, since it is the pivot index
            to start calculating the tail, which extends backward.
          - The start index will be before the end index, and will be considered.
          - Then we subtract (tail_size - 1) to the start index: for each index
            iteration, we should consider the start of its tail is exactly
            (tail_size - 1) steps behind, and includes this step as the last.
          - However, when computing slices, it may occur that such new index is
            below 0, so we truncate it to 0. In such cases, the slicing will
            have less elements than following slices.

        An array is returned, which may actually have less elements than the
          result of (end - start + tail_size - 1), if the data has less elements.
        :param data: The data or source being sliced.
        :param start: The start index - usually in the context of an update operation.
        :param end: The end index - usually in the context of an update operation.
        :param tail_size: The tail size.
        :return: A slice of the given data.
        """

        return data[max(0, start + 1 - tail_size):end]

    def _tail_iterate(self, data, start, end, tail_size):
        """
        Teaming with the _tail_slice utility method, returns a generator which will
          iterate over the given data (which will most often be a dependency of the
          same scale), appropriately indexed to get the tail start, the tail end,
          whether a complete tail was fetched this iteration, and the actual slice
          of data corresponding to this iteration, given the overall start, end,
          and tail size for the given data.
        :param data: The data being iterated. It was already sliced by _tail_size.
        :param start: The start index - usually in the context of an update operation.
        :param end: The end index - usually in the context of an update operation.
        :param tail_size: The tail size.
        :return: A generator yielding tuples like:
          (local tail start index,
           local tail end index,
           tail is incomplete,
           global index)
        """

        offset = data.shape[0] - end + start
        for idx in range(0, end - start):
            tail_end = idx + 1 + offset
            tail_start = tail_end - tail_size
            incomplete = False
            if tail_start < 0:
                tail_start = 0
                incomplete = True
            yield tail_start, tail_end, incomplete, start + idx

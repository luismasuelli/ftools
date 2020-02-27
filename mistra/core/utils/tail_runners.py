class TailRunner:
    """
    A TailRunner works by appropriately fetching data to be iterated
      by overlapping chunks ("tails") ending in the desired (iterated)
      index, and of an -at most // when "complete"- size.
    """

    def __init__(self, tail_size):
        if not isinstance(tail_size, int) or tail_size <= 1:
            raise ValueError("Tail size must be an integer greater than 1")
        self._tail_size = tail_size

    @property
    def tail_size(self):
        return self._tail_size

    @staticmethod
    def _tail_slice(data, start, end, tail_size):
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

    @staticmethod
    def _tail_iterate(data, start, end, tail_size):
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

    def tail_iterate(self, start, end, source):
        """
        Iterates over the [start:end] indices (not including the
          end) to get a tail, of the chosen tail size, ending in
          the index being iterated.
        :param start: The start index.
        :param end: The end index.
        :param source: The source of the iterator.
        :return: An iterator yielding (index, tail, incomplete)
          being the current end index, the tail, and a flag telling
          whether the tail is full-size or not (depending on the
          chosen index).
        """

        data = self._tail_slice(source, start, end, self._tail_size)
        for tail_start, tail_end, incomplete, idx in self._tail_iterate(data, start, end, self._tail_size):
            yield idx, data[tail_start:tail_end], incomplete

from numpy import array, ndarray


class GrowingArray:
    """
    A growing array can grow, but never shrink. Every time new data needs to be added, the array will
      perhaps grow to cover the required indices. Several chunks (all of the same size) will be created
      on demand if a large index or a large slice -in both cases: before the current end- is provided.

    When getting an item or slice, IndexError will be raised as usual if out of bounds. Aside from that,
      data will be gathered across several different chunks if needed.

    In any case, negative indices are NOT supported, and steps different to 1 in slices are neither.
    """

    def __init__(self, dtype, chunk_size=3600, width=1):
        if chunk_size < 60:
            raise ValueError("Chunk size cannot be lower than 60")
        if width < 1:
            raise ValueError("Width cannot be lower than 1")
        self._chunks = []
        self._dtype = dtype
        self._chunk_size = chunk_size
        self._width = width
        self._max_stop = 0

    def __getitem__(self, item):
        """
        Gets an element, or a numpy array of elements, given the index or slice.
        :param item: The index or slice to get the value from.
        :return: A numpy array with the specified items, if slice, or a single element.
        """

        if isinstance(item, slice):
            start = item.start
            stop = item.stop
            if start < 0 or stop < 0:
                raise KeyError("Negative indices in slices are not supported")
            if stop < start:
                raise KeyError("Slices must have start <= stop indices")
            elif stop == start:
                return
            if item.step != 1:
                raise KeyError("Slices with step != 1 are not supported")
        elif isinstance(item, int):
            if item < 0:
                raise IndexError("Negative indices are not supported")
            start = item
            stop = None
        else:
            raise TypeError("Only slices or integer indices are supported")
        if start >= self._max_stop or stop > stop:
            raise IndexError(item)
        return self._gather(start, stop)

    def _gather(self, start, stop):
        """
        Gathers required data from chunk(s).
        :param start: The start index to start gathering from.
        :param stop: The stop index (not included) to stop gathering from.
        :return: The gathered data (a single element, or a numpy array).
        """

        # TODO

    def _allocate(self, stop):
        """
        Allocates new arrays as needed, when needed, if needed.
        :param stop: The requested stop index.
        """

        chunks_count = len(self._chunks)
        total_allocated = chunks_count * self._chunk_size
        if stop > total_allocated:
            new_bins = (stop + self._chunk_size - 1)//self._chunk_size - chunks_count
            for _ in range(0, new_bins):
                self._chunks.append(array((self._chunk_size,), dtype=self._dtype))
        self._max_stop = max(self._max_stop, stop)

    def _fill(self, start, stop, data):
        """
        Fills chunk(s) contents with given data.
        :param start: The start index to start filling.
        :param stop: The stop index (not included) to stop filling.
        :param data: The data to fill with.
        :return:
        """

        # TODO

    def __setitem__(self, key, value):
        """
        Sets an element, or a numpy array of elements, given the index or slice.
        Chunks may be created on demand, depending on the index or slice being set.
        :param key: The index or slice to set the value into.
        :param value: The value to set.
        """

        if isinstance(key, slice):
            start = key.start
            stop = key.stop
            if start < 0 or stop < 0:
                raise KeyError("Negative indices in slices are not supported")
            if stop < start:
                raise KeyError("Slices must have start <= stop indices")
            elif stop == start:
                return
            if key.step != 1:
                raise KeyError("Slices with step != 1 are not supported")
            if not isinstance(value, ndarray) or value.shape != (stop - start,):
                raise TypeError("When setting a slice, the value must be a numpy array of (stop - start)x1 elements")
        elif isinstance(key, int):
            if key < 0:
                raise IndexError("Negative indices are not supported")
            start = key
            stop = None
            if isinstance(value, ndarray):
                raise TypeError("When setting an index, the value must not be a numpy array")
        else:
            raise TypeError("Only slices or integer indices are supported")
        self._allocate(stop)
        self._fill(start, stop, value)

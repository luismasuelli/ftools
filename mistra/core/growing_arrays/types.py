from numpy import zeros, full
from .support import chunked_slicing, fix_slicing, fix_input


class GrowingArray:
    """
    A growing array can grow, but never shrink. Every time new data needs to be added, the array will
      perhaps grow to cover the required indices. Several chunks (all the same size) will be created
      on demand if a large index or a large slice -in both cases: before the current end- is provided.

    When getting an item or slice, IndexError will be raised as usual if out of bounds. Aside from that,
      data will be gathered across several different chunks if needed.

    In any case, negative indices are NOT supported, and steps different to 1 in slices are neither.
    """

    def __init__(self, dtype, fill_value, chunk_size=3600, width=1):
        if not isinstance(chunk_size, int) or chunk_size < 4:
            raise ValueError("Chunk size cannot be lower than 60")
        if not isinstance(width, int) or width < 1:
            raise ValueError("Width cannot be lower than 1")
        self._chunks = []
        self._dtype = dtype
        self._chunk_size = chunk_size
        self._fill_value = fill_value
        self._width = width
        self._length = 0

    @property
    def dtype(self):
        return self._dtype

    @property
    def width(self):
        return self._width

    def __getitem__(self, item):
        """
        Gets an element, or a numpy array of elements, given the index or slice.
        :param item: The index or slice to get the value from.
        :return: A numpy array with the specified items, if slice, or a single element.
        """

        start, stop, column = fix_slicing(item, self._length)
        return self._gather(start, stop, column)

    def _gather(self, start, stop, column):
        """
        Gathers required data from chunk(s).
        :param start: The start index to start gathering from.
        :param stop: The stop index (not included) to stop gathering from. It will be None if only one
          single element (a number or a (1, width) vector) is being retrieved.
        :param column: The column index or slice to retrieve a subset of the columns instead.
          If None, all the columns will be retrieved.
        :return: The gathered data (a single element, or a numpy array).
        """

        if stop is None:
            chunk_index = start // self._chunk_size
            chunk_pos = start % self._chunk_size
            chunk = self._chunks[chunk_index][chunk_pos]
            return chunk[:] if column is None else chunk[column]
        else:
            if isinstance(column, int):
                column = slice(column, column + 1, 1)
            elif column is None:
                column = slice(0, self._width, 1)
            if isinstance(column, slice):
                width = len(range(*column.indices(self._width)))
            else:
                raise IndexError("The second index to retrieve, if specified, must be an integer or a slice")
            data = zeros((stop-start, width), dtype=self._dtype)
            chunkings = chunked_slicing(start, stop, self._chunk_size)
            for (data_start, data_stop), chunk, (chunk_start, chunk_stop) in chunkings:
                data[data_start:data_stop, :] = self._chunks[chunk][chunk_start:chunk_stop, column]
            return data

    def _allocate(self, stop):
        """
        Allocates new arrays as needed, when needed, if needed.
        :param stop: The requested stop index.
        """

        chunks_count = len(self._chunks)
        total_allocated = chunks_count * self._chunk_size
        if stop > total_allocated:
            new_bins = (stop + self._chunk_size - 1) // self._chunk_size - chunks_count
            for _ in range(0, new_bins):
                arr = full((self._chunk_size, self._width), dtype=self._dtype, fill_value=self._fill_value)
                self._chunks.append(arr)
        self._length = max(self._length, stop)

    def _fill(self, start, stop, data):
        """
        Fills chunk(s) contents with given data.
        :param start: The start index to start filling.
        :param stop: The stop index (not included) to stop filling. It will be None if only one
          single element is being set.
        :param data: The data to fill with.
        :return:
        """

        if stop is None:
            chunk_index = start // self._chunk_size
            chunk_pos = start % self._chunk_size
            self._chunks[chunk_index][chunk_pos] = data
        else:
            chunkings = chunked_slicing(start, stop, self._chunk_size)
            for (data_start, data_stop), chunk, (chunk_start, chunk_stop) in chunkings:
                self._chunks[chunk][chunk_start:chunk_stop] = data[data_start:data_stop]

    def __setitem__(self, key, value):
        """
        Sets an element, or a numpy array of elements, given the index or slice.
        Chunks may be created on demand, depending on the index or slice being set.
        :param key: The index or slice to set the value into.
        :param value: The value to set.
        """

        start, stop, _ = fix_slicing(key, None, False)
        if stop is not None:
            value = fix_input(key, self._width, stop - start, self._dtype, value)
            self._allocate(stop)
            if stop > start:
                self._fill(start, stop, value)
        else:
            value = fix_input(key, self._width, 1, self._dtype, value)
            self._allocate(start + 1)
            self._fill(start, stop, value)

    def __repr__(self):
        return "GrowingArray(%s)" % ', '.join(str(chunk) for chunk in self._chunks)

    def __str__(self):
        return repr(self)

    def __len__(self):
        return self._length

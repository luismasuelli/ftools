from numpy import ndarray, array


def fix_slicing(index, logical_length):
    """
    Checks, and caps, the slices being used.
    :param index: The initial index, which may be int or slice.
    :param logical_length: The current logical length of the data.
    :return: The fixed slicing, if no exception occurs.
    """

    if isinstance(index, slice):
        if index.step and index.step != 1:
            raise KeyError("Slices with step != 1 are not supported")
        if slice.start < 0 or slice.stop < 0:
            raise KeyError("Negative indices in slices are not supported")
        if slice.stop < slice.start:
            raise KeyError("Slices must have start <= stop indices")
        else:
            # Here, start will be <= stop. We will limit both by the logical_length, silently.
            return min(slice.start, logical_length), min(slice.stop, logical_length)
    elif isinstance(index, int):
        if index < 0:
            raise IndexError("Negative indices are not supported")
        return min(index, logical_length), None
    else:
        raise TypeError("Only slices (non-negative, growing, and with step 1) or non-negative integer indices are "
                        "supported")


def fix_input(index, expected_width, expected_length, value):
    """
    Checks and fixes the value according to the given index type.
    :param index: The initial index, which may be int or slice.
    :param expected_width: The expected width of the value.
    :param expected_length: The expected length of the data. It will be ignored if the index is a number.
    :param value: The given value, which may be scalar or array.
    :return: The fixed value, if no exception occurs.
    """

    if isinstance(index, slice):
        if not isinstance(value, ndarray):
            raise TypeError("When setting a slice, the value must be a numpy array of (stop - start)x(width) "
                            "elements (if the width is 1, an uni-dimensional array of (stop-start) elements is "
                            "also allowed)")
        if expected_width == 1 and len(value.shape) == 1:
            value = value[:]
            value.shape = (value.size, 1)
        if value.shape != (expected_length, expected_width):
            raise TypeError("When setting a slice, the value must be a numpy array of (stop - start)x(width) "
                            "elements (if the width is 1, an uni-dimensional array of (stop-start) elements is "
                            "also allowed)")
    elif isinstance(index, int):
        if expected_width > 1 and not isinstance(value, ndarray):
            raise TypeError("When setting an index, the value must not be a numpy array if the width is > 1")
        if expected_width == 1 and isinstance(value, int):
            value = array((value,))
    else:
        raise TypeError("Only slices (non-negative, growing, and with step 1) or non-negative integer indices are "
                        "supported")
    return value


def chunked_slicing(slice_start, slice_stop, chunk_size):
    """
    Iterator that yields, every time, a data structure like this:
      - Current chunk index
      - Start index in chunk
      - Stop index in chunk
      - Start index in source/destination
      - Stop index in source/destination

    It is guaranteed: 0 <= slice_start <= slice_stop <= logical length <= chunk_size * chunk_count.

    The algorithm goes like this:
      - Before: we know the starter bin, and the end bin.
    :param slice_start: The overall start.
    :param slice_stop: The overall stop.
    :param chunk_size: The chunk size.
    :return: A generator.
    """

    start_chunk = slice_start // chunk_size
    stop_chunk = slice_stop // chunk_size
    if start_chunk == stop_chunk:
        # This is the easiest case.
        # The data indices will be 0 and stop_chunk - start_chunk.
        # The chunk index will be start_chunk.
        # the start index in chunk, and end index in chunk, will both involve modulo.
        data_indices = (0, slice_stop - slice_start)
        chunk_indices = (slice_start % chunk_size, slice_stop % chunk_size)
        yield data_indices, start_chunk, chunk_indices
    else:
        # In this case, start chunk will always be lower than end chunk.
        chunk_start_index = slice_start % chunk_size
        chunk_stop_index = slice_stop % chunk_size
        first_iteration = True
        data_index = 0
        current_chunk = start_chunk
        # We know that, in the first iteration:
        # - chunk_start_index >= 0
        # - start_chunk < stop_chunk, strictly
        # And in further iterations:
        # - chunk_start_index == 0
        # - start_chunk <= stop_chunk
        while True:
            # The chunk upper bound will be:
            # - The chunk stop index, if in last chunk.
            # - The chunk size, otherwise.
            if current_chunk == stop_chunk:
                # Another check here: if the chunk stop index is 0, just break.
                if chunk_stop_index == 0:
                    return
                current_chunk_ubound = chunk_stop_index
            else:
                current_chunk_ubound = chunk_size
            # The chunk lower bound will be:
            # - The chunk start index, if in first chunk.
            # - 0, otherwise.
            if first_iteration:
                current_chunk_lbound = chunk_start_index
            else:
                current_chunk_lbound = 0
            # Now we know the chunk start and chunk end bounds.
            # We also know the current chunk index.
            # We also know the current data index.
            # Also we can compute the current data length
            length = current_chunk_ubound - current_chunk_lbound
            # We can yield all the data now.
            data_indices = (data_index, data_index + length)
            chunk_indices = (current_chunk_lbound, current_chunk_ubound)
            yield data_indices, current_chunk, chunk_indices
            # If this is the last chunk, we must exit.
            if current_chunk == stop_chunk:
                return
            # If not, then we move the data index and the current chunk.
            current_chunk += 1
            data_index += length

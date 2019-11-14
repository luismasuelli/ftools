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

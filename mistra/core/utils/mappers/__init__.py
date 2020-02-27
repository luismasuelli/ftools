from numpy import array


def map(source, item, function, dtype):
    """
    Given a "source" (an arbitrary object supporting 1-dimensional
      slicing and returning an arbitrary numpy array), it gets an
      item (which may be using an individual index, or a slice) and
      applies a mapping function depending the case: item or slice,
      and returning depending on the case: individual mapped item,
      or a numpy array of mapped values.
    :param source: The source to get the item from.
    :param item: The item to get, which may be int or slice.
    :param function: The mapping function to apply.
    :param dtype: The dtype to give the resulting array.
    :return: The mapped value.
    """

    data = source[item]
    if isinstance(item, slice):
        mapped = list(function(data[idx]) for idx in range(data.shape[0]))
        return array(mapped, dtype=dtype)
    elif isinstance(item, int):
        return function(data)
    else:
        raise TypeError("Unsupported item index type. Expected: slice or int")

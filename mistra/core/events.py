class Event:
    """
    Callbacks can be registered/unregistered to the event,
      and the event can be triggered.
    """

    def __init__(self):
        self._callbacks = set()

    def register(self, callback):
        self._callbacks.add(callback)

    def unregister(self, callback):
        self._callbacks.discard(callback)

    def trigger(self, *args, **kwargs):
        for callback in self._callbacks:
            callback(*args, **kwargs)

    def listeners(self):
        """
        Iterates over all the registered listener methods and their
          bound receivers.
        :return: A generator.
        """
        for callback in self._callbacks:
            yield callback, getattr(callback, '__self__', None)

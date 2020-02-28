class Instrument:
    """
    Instruments belong to a connection, and under a specific instrument key.

    The lifecycle of the instrument goes like this:
      - Creation: The constructor must enable the needed components of an
        instrument.
      - dispose(): This method is called on disposal of an instrument, but
        never meant to be used by the instrument directly, but only invoked
        by a parent connection.
      - activate(): This method is called when the connection, actually,
        connects, and also called when the instrument is added to a connection
        (created inside an add_instrument call) and the connection is, actually,
        connected.
      - deactivate(): This method is called when the connection disconnects,
        and also when the instrument is disposed (even if the connection is
        still connected).
    Creating an instrument or calling dispose() are not things meant to be
      invoked directly, but the activate()/deactivate() methods may be. They
      look more like a pause/resume feature.
    """

    def __init__(self, connection, key):
        self._connection = connection
        self._key = key

    @property
    def connection(self):
        return self._connection

    @property
    def key(self):
        return self._key

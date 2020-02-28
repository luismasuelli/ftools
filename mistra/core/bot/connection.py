from ..events import Event


class Connection:
    """
    The client connection the bot uses for its activity. It retains most of the
      functionality, and provides events and data related to the connection.

    All the connections will provide these features:
      - A connection status telling whether an account is successfully logged in
        or not. This also implies the fact that the connection is established,
        in stateful interactions. For stateless interactions, this status is set
        to true when it is first-time fetched, and set to false when somehow the
        access is deemed as invalid by the endpoint(s).
      - Several "representational" fields involving the connection and current
        account. These fields are a representation -since the true data is
        actually internal and managed by the connection itself- to be used in an
        UI or be printed to the user. The fields are:
        - Connection string: Will always exist. It will usually represent a host,
          but there MAY exist the case where the connection string is an url that
          also includes the account.
        - Account ID: It may involve the account number, the username, or even a
          combination of both in some APIs supporting account and sub-account.
        - Account Display: This one may even be empty. It is a label holding a
          description of the account, like the real name.
        - Funds: A float number with the funds of this account (or sub account).

    Regarding the connection and account, these events will be available:
      - on_connected: A connection was successfully established.
      - on_rejected: A connection was failed to establish.
      - on_disconnected: A connection was terminated.
    While this make a lot of sense regarding stateful connections, stateless ones
      should report on_connected while trying to fetch the account data from the
      appropriate account endpoint and succeeding, should report on_rejected when
      trying to access such endpoint and failing by having invalid credentials (or
      having a connection error), and on_disconnected when trying to access an
      endpoint with the in-use credentials... that are no longer valid somehow.

    Signatures:
      - Callbacks for on_connected take one argument: This object.
      - Callbacks for on_rejected take two arguments: This object and the reason.
      - Callbacks for on_disconnected take two arguments: This object and the reason.

    Regarding the account management, some data will never or seldom be updated
      (e.g. account id, or display name). This is not the case of the funds: they
      will be updated frequently. Stateful connection will have this one quite
      easy to do, but stateless may need to use some workarounds like periodically
      polling the data. To report an account data update, the following event will
      be triggered:
      - on_update: The account data was updated.

    Signatures: The callbacks for this event take one argument: this connection
      object. The listener will use this object to retrieve the account data.

    Connection objects maintain a connection setting (say: host, account) and can
      perform only one connection at the same time, but that connection may be
      terminated, restarted, and continued (this is useful for market data and the
      indicators so they don't have to be recalculated on each reboot). Two methods
      allow the user to connect and disconnect:
      - connect(): Attempts to establish a connection. On success, the on_connected
        event will be triggered. On failure, the on_rejected event will be triggered.
      - disconnect(): Attempts to disconnect, if connected. On disconnection, the
        on_disconnected event will be triggered, and its reason will refer the
        user-request to disconnect.
    These methods are totally implementation-specific.

    Once a connection is defined, instruments can be managed in this connection and
      then reflected also via events that can be listened for. These events come as
      follows:
      - on_instrument_added: Tells when the connection configured a new instrument.
      - on_instrument_disposed: Tells when the connection disposed an instrument.
    These events may trigger even if there's currently no connection, because the
      instruments may be added regardless the connection status. They should tell the
      listening UI to add or remove, say, a new "tab" with the involved instrument.
      Adding an instrument doesn't tell whether the instrument is "ready" (say: to
      receive / update market data) - this only occurs when the instrument is
      successfully added and a connection is alive. Instruments will triggers their
      own events regarding that).

    Signatures: The callbacks for both events take two arguments: This object and the
      instrument object.

    Finally, there are these methods used to manage instruments:
      - get_supported_instruments(): Lists the instruments supported by this broker.
      - add_instrument(code): Adds an instrument. It does nothing if the instrument
        is already added. On success, the on_instrument_added is disposed.
      - dispose_instrument(code): Disposes an instrument. It does nothing if the
        instrument is not present. Disposing an instrument is a per-instrument
        behaviour, but this connection object executes that behaviour and then
        removes the instrument from this list, and triggers on_instrument_disposed.
    """

    def __init__(self):
        self._connection_string = None
        self._account_id = None
        self._account_dislpay = None
        self._funds = None
        self._on_connected = Event()
        self._on_rejected = Event()
        self._on_disconnected = Event()
        self._on_instrument_added = Event()
        self._on_instrument_disposed = Event()
        self._on_update = Event()
        self._instruments = {}

    def _connect(self, on_success, on_failed):
        """
        Attempts a connection. If the connection succeeds, this method must invoke the
          on_success callback with no arguments. If it fails, it must invoke the on_failed
          callback with the reason as an argument.

        This method is implementation-specific. It is mandatory to implement it somehow.

        :param on_success: The callback to invoke when the connection succeeded.
        :param on_failed: The callback to invoke when the connection failed.
        """

        raise NotImplemented

    def _disconnect(self, on_disconnected):
        """
        Attempts a disconnection. This is a user-requested disconnection and must invoke
          on_disconnected with no arguments on success.

        This method is implementation-specific. It is mandatory to implement it somehow.

        :param on_disconnected: The callback to invoke when the connection terminated.
        """

        raise NotImplemented

    def _is_connected(self):
        """
        Reports whether a connection is established.

        This method is implementation-specific. It is mandatory to implement it somehow.

        :return: a boolean answer telling whether a valid connection (and authentication)
          is established.
        """

        raise NotImplemented

    def _get_supported_instruments(self):
        """
        Retrieves the supported instruments as a dictionary.
        - In their keys: the instrument key/code (e.g. EUR_USD). The code structure is
          implementation-specific and will remain constant (for each connection knows
          how to handle each code and its format).
        - In their values: arbitrary data - understanding it is implementation-specific.

        This method is implementation-specific. It is mandatory to implement it somehow.

        :return: A dictionary with the supported instruments by this implementation.
        """

        raise NotImplemented

    def _create_instrument(self, key):
        """
        Instantiates an instrument.

        This method is implementation-specific. It is mandatory to implement it somehow.

        :return: The instrument instance.
        """

        raise NotImplemented

    def connect(self):
        """
        Attempts a connection. On success, it attempts to activate all of the existing instruments.

        This method invokes a method that must be implemented because it is per-implementation.
        """

        def on_success():
            for key, instrument in self._instruments:
                instrument.activate()
            self._on_connected.trigger(self)

        def on_failed(reason):
            self._on_rejected.trigger(self, reason)

        self._connect(on_success, on_failed)

    def disconnect(self):
        """
        Attempts a disconnection. Returns False if there was no connection beforehand,
          and returns True otherwise.

        This method invokes a method that must be implemented because it is per-implementation.

        :return: Whether a disconnection was/will-be made, or not (because it was already not
          connected).
        """

        if self._is_connected():
            def on_disconnect():
                for key, instrument in self._instruments:
                    instrument.deactivate()
                self._on_disconnected.trigger(self, None)
            self._disconnect(on_disconnect)
            return True
        else:
            return False

    @property
    def connected(self):
        """
        Reports whether a connection is established. As long as this property returns True,
          all the other public fields may be considered stable. If this property is False,
          only the connection string and account id may be considered stable.

        This property invokes a method that must be implemented because it is per-implementation.

        :return: a boolean answer telling whether a valid connection (and authentication)
          is established.
        """

        return self._is_connected()

    def get_supported_instruments(self):
        """
        Returns None if no connection is performed. Otherwise, retrieves the supported
          instruments as a dictionary.
          - In their keys: the instrument key/code (e.g. EUR_USD). The code structure is
            implementation-specific and will remain constant (for each connection knows
            how to handle each code and its format).
          - In their values: arbitrary data - understanding it is implementation-specific.

        This method invokes a method that must be implemented because it is per-implementation.

        :return: None, or a dictionary.
        """

        if self._is_connected():
            return self._get_supported_instruments()
        else:
            return None

    def add_instrument(self, key):
        """
        Creates an instrument by its key. The instrument instance will be created and, if the
          connection is ready, it will also be "enabled".

        This property invokes methods that must be implemented because it is per-implementation.

        :param key: The instrument key to use.
        :return: The instrument, whether it is
        """

        if key not in self._instruments:
            self._instruments[key] = self._create_instrument(key)
        instrument = self._instruments[key]
        self._on_instrument_added.trigger(self, instrument)
        if self._is_connected():
            instrument.activate()
        return instrument

    def dispose_instrument(self, key):
        """
        Disposes an instrument, if present, by its key. The instrument will be called to disposal
          (it will deactivate beforehand, if active).

        This property invokes methods that must be implemented because it is per-implementation.

        :param key: The key of the instrument to dispose.
        :return: Whether the instrument was disposed, or not (because it is not present).
        """

        if key not in self._instruments:
            return False
        instrument = self._instruments[key]
        if self._is_connected():
            instrument.deactivate()
        instrument.dispose()
        self._on_instrument_disposed.trigger(self, instrument)
        return True

    @property
    def connection_string(self):
        return self._connection_string

    @property
    def account_id(self):
        return self._account_id

    @property
    def account_display(self):
        return self._account_dislpay

    @property
    def funds(self):
        return self._funds

    @property
    def on_connected(self):
        return self._on_connected

    @property
    def on_rejected(self):
        return self._on_rejected

    @property
    def on_disconnected(self):
        return self._on_disconnected

    @property
    def on_update(self):
        return self._on_update

    @property
    def on_instrument_added(self):
        return self._on_instrument_added

    @property
    def on_instrument_disposed(self):
        return self._on_instrument_disposed


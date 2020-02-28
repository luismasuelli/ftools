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
    """

    def __init__(self):
        self._connection_string = None
        self._account_id = None
        self._account_dislpay = None
        self._funds = None
        self._on_connected = Event()
        self._on_rejected = Event()
        self._on_disconnected = Event()
        self._on_update = Event()

    def _is_connected(self):
        """
        Reports whether a connection is established.

        This method is implementation-specific. It is mandatory to implement it somehow.

        :return: a boolean answer telling whether a valid connection (and authentication)
          is established.
        """

        raise NotImplemented

    def connect(self):
        """
        Attempts a connection.

        This method is implementation-specific. It is mandatory to implement it somehow.

        Must trigger on_connected or on_rejected.
        """

        raise NotImplemented

    def disconnect(self):
        """
        Attempts a disconnection. Returns False if there was no connection beforehand,
          and returns True otherwise.

        This method is implementation-specific. It is mandatory to implement it somehow.

        Must trigger on_disconnected, on disconnection, with user-request reason.

        :return: Whether a disconnection was made, or not.
        """

        raise NotImplemented

    @property
    def connected(self):
        """
        Reports whether a connection is established. As long as this property returns True,
          all the other public fields may be considered stable. If this property is False,
          only the connection string and account id may be considered stable.

        This field invoked a method that must be implemented because it is per-implementation.

        :return: a boolean answer telling whether a valid connection (and authentication)
          is established.
        """

        return self._is_connected()

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


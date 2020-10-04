class IdentityMapper:
    """
    Identity mappers return the values as unchanged.

    Their only purpose is either debugging or as a readonly proxy.
    """

    def __init__(self, parent):
        self._parent = parent

    def __getitem__(self, item):
        return self._parent[item]

    def __len__(self):
        return len(self._parent)

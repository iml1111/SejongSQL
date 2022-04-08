from urllib.parse import urlparse


class URI:
    """URI Controller"""

    def __init__(self, uri: str):
        if not isinstance(uri, str):
            raise TypeError('uri must be "str".')
        dbc = urlparse(uri)
        self.scheme = dbc.scheme or None
        self.hostname = dbc.hostname or None
        self.username = dbc.username or None
        self.password = dbc.password or None
        self.dbname = dbc.path.lstrip('/') or None
        try:
            self.port = dbc.port
        except ValueError:
            self.port = None

    def __str__(self):
        return (
            f"(scheme={self.scheme}, "
            f"hostname={self.hostname}, "
            f"port={self.port}, "
            f"username={self.username}, "
            f"password={self.password}, "
            f"dbname={self.dbname})"
        )

    def __repr__(self):
        return self.__str__()

    @property
    def is_valid(self):
        return (
            None not in (
                self.scheme,
                self.hostname, self.port,
                self.username, self.password,
                self.dbname,
            )
        )


if __name__ == '__main__':
    a = 'mysql://username:password@host:asd0/asd'
    uri = URI(a)
    print(uri.is_valid)
    print(uri)
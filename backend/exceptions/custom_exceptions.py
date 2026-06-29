class SearchEngineError(Exception):
    """Base Exception"""
    pass


class DataFileNotFound(SearchEngineError):
    pass


class IndexNotFound(SearchEngineError):
    pass


class InvalidQuery(SearchEngineError):
    pass
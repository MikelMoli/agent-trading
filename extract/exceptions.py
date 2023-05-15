
class AssetNotValidException(Exception):
    """
        Specied asset is not included in the config file. This could mean that the asset is not available in the source.
    """


class InvalidYearRangeValuesException(Exception):
    """
        Specified start year or end year are not valid.
    """


class AssetsNotSpecifiedException(Exception):
    """
        Assets for extraction haven't been specified
    """


class ResourceNotFoundException(Exception):
    """
        Specified URL returns a 404. Check if the URL is malformed or if the resource doesn't exist in the source.
    """


class StartYearGreaterThanEndYearException(Exception):
    """
        Specified start year is bigger than the end year
    """


class InvalidOutputFileTypeException(Exception):
    """
        Specified output file type is not valid
    """


class ColumnNamesMisinterpreted(Exception):
    """
        Specified columns do not match with its values
    """

import os
from typing import List

import config
import logging
logging.basicConfig(level=logging.INFO)
from datetime import datetime
from abc import ABC, abstractmethod
from exceptions import AssetNotValidException, InvalidYearRangeValuesException, AssetsNotSpecifiedException


class ExtractBase(ABC):

    def __init__(self, market: str, assets: List[str], start_year: int, end_year: int):
        self._logger = logging.getLogger("extract_logger")
        self._logger.setLevel(logging.DEBUG)
        self._market = market
        self._assets = assets
        self._start_year = start_year
        self._end_year = end_year
        self._source_url = config.SOURCES[market]
        self._create_basic_folder_structure()
        self._validate_data_inputs()

    def _validate_data_inputs(self) -> None:
        if self._start_year < 2015 or self._end_year > datetime.now().year:
            raise InvalidYearRangeValuesException("Specified start year or end year are invalid due to source. Please,"
                                                  f" specify values between 2015 and {datetime.now().year} both included.")
        if len(self._assets) == 0:
            raise AssetsNotSpecifiedException("Assets haven't been specified. Please, specify them using the parameter assets.")
        self._check_asset_validity()

    def _create_basic_folder_structure(self) -> None:
        os.makedirs(os.path.join(config.DATA_FOLDER_PATH, self._market, "merged"), exist_ok=True)
        os.makedirs(os.path.join(config.DATA_FOLDER_PATH, "merged"), exist_ok=True)

    def _check_asset_validity(self) -> None:
        invalid_assets = []
        for asset in self._assets:
            if asset not in config.VALID_ASSETS[self._market]:
                invalid_assets.append(asset)
            else:
                for year in range(self._start_year, self._end_year+1):
                    asset_year_folder_path = os.path.join(config.DATA_FOLDER_PATH, self._market, asset, str(year))
                    os.makedirs(asset_year_folder_path, exist_ok=True)

        if len(invalid_assets) > 0:
            raise AssetNotValidException(f"Next assets are not specified in the {self._market} section of the VALID_ASSETS "
                                         f"dict in the config file: \n {invalid_assets} \nThis could mean that these assets "
                                         f"are not available in the source website or that they have not been contemplated. "
                                         f"Please, remove them from the arguments or add them in the config file.")

    @abstractmethod
    def _extract_data(self) -> None:
        return

    @abstractmethod
    def _merge_data(self) -> None:
        return

import os
import sys
import logging
from typing import List

import pandas as pd

logging.basicConfig(level=logging.INFO)

import argparse
from exceptions import StartYearGreaterThanEndYearException, AssetNotValidException, InvalidOutputFileTypeException
from extract_forex import ExtractForex
from datetime import datetime
sys.path.append(os.getcwd())

import config
from extract.extract_forex import ExtractForex


class ExtractionHandler:

    def __init__(self, extraction_asset_list: List[str], start_year: int, end_year: int, output_format: str):
        self._logger = logging.getLogger("EXTRACTION_HANDLER")
        self._logger.setLevel(logging.INFO)
        self._split_assets(extraction_asset_list)
        self._validate_or_populate_arguments(start_year, end_year, output_format)

    def _split_assets(self, extraction_asset_list: List[str]) -> None:
        valid_assets = []
        self._assets = dict()
        for market, asset_list in config.VALID_ASSETS.items():
            market_specific_assets = []

            for asset in extraction_asset_list:
                if asset in asset_list:
                    market_specific_assets.append(asset)
                    valid_assets.append(asset)

            self._assets[market] = market_specific_assets

        invalid_assets = [asset for asset in extraction_asset_list if asset not in valid_assets]
        if len(invalid_assets) > 0:
            raise AssetNotValidException(f"{invalid_assets} are not included in config file. Please, delete or correct them.")

    def _validate_or_populate_arguments(self, start_year: int, end_year: int, output_format: str) -> None:
        if start_year is None:
            self._start_year = config.EXTRACTION_DEFAULT_END_YEAR
            self._logger.info(f"Start year not specified, defaulting to year: {self._start_year}")
        else:
            self._start_year = start_year

        current_year = datetime.now().year
        if end_year is None:
            self._end_year = current_year
            self._logger.info(f"End year not specified, defaulting to current year: {self._end_year}")
        else:
            self._end_year = end_year

        if self._start_year > self._end_year:
            raise StartYearGreaterThanEndYearException("Start year greater than end year... Please correct argument values")

        if self._end_year > current_year:
            self._end_year = current_year
            self._logger.info(f"End year is invalid, defaulting to current year: {current_year}")

        if output_format is None:
            self._output_format = 'parquet'
            self._logger.info(f"Output format not specified, defaulting to parquet")
        elif output_format.lower() not in config.VALID_FILE_OUTPUT_FORMATS:
            raise InvalidOutputFileTypeException(f"Specified output file format {output_format} is not valid. Please, insert one of these values {config.VALID_FILE_OUTPUT_FORMATS}")
        else:
            self._output_format = output_format

    def _merge_data(self) -> None:
        self._logger.info('Merging all data...')
        final_df = pd.DataFrame()
        for market in config.VALID_ASSETS.keys():
            filepath = os.path.join(config.DATA_FOLDER_PATH, market, 'merged')
            try:
                market_files = os.listdir(filepath)
                if len(market_files) == 1:
                    aux_df = pd.read_parquet(os.path.join(filepath, f'{market}.parquet'))
                final_df = pd.concat([final_df, aux_df], axis=0, ignore_index=True)
            except FileNotFoundError:
                """ Crypto and commodities are not implemented so it will fail to create the folders """
        final_filename = 'complete_data'
        if self._output_format == "csv":
            final_df.to_csv(os.path.join(config.DATA_FOLDER_PATH, 'merged', f'{final_filename}.csv'), index=False, encoding='utf-8')
        elif self._output_format == "parquet":
            final_df.to_parquet(os.path.join(config.DATA_FOLDER_PATH, 'merged', f'{final_filename}.parquet'), index=False)

    def run(self) -> None:
        ExtractForex(assets=self._assets['forex'], start_year=self._start_year, end_year=self._end_year).run()
        # TODO: Add crypto
        # TODO: Add commodities
        self._merge_data()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--assets', '--activos', dest='assets', nargs='+', help='Assets to extract', required=True)
    parser.add_argument('-s', '--start', '--inicio', dest='start_year', help='Extraction start year', type=int)
    parser.add_argument('-e', '--end', '--fin', dest='end_year', help='Extraction end year', type=int)
    parser.add_argument('-o', '--output', dest='output_format', help='Output file format', type=str)
    args = parser.parse_args()

    eh = ExtractionHandler(extraction_asset_list=args.assets, start_year=args.start_year, end_year=args.end_year, output_format=args.output_format)
    eh.run()

import os
import sys
import pyarrow

from typing import List

sys.path.append(os.getcwd())
import shutil
import config
import requests
import zipfile
import pandas as pd

from extract_base import ExtractBase
from exceptions import ResourceNotFoundException, ColumnNamesMisinterpreted


class ExtractForex(ExtractBase):

    def __init__(self, market: str = 'forex', assets: List[str] = ['USDEUR'], start_year: int = 2017, end_year: int = 2023):
        super().__init__(market, assets, start_year, end_year)

    def _extract_data(self):
        index = 0
        for currency_pair in self._assets:
            index += 1
            self._logger.info(f"Extracting {index}/{len(self._assets)} -  {currency_pair}...")
            for year in range(self._start_year, self._end_year + 1):
                try:
                    self._download_and_unzip_files(str(year), currency_pair)
                except ResourceNotFoundException as e:
                    self._logger.exception(f"[404 ERROR]: URL for year {year} and currency pair: {currency_pair} haven't been found. Continuing extraction...")

    @staticmethod
    def clean_directories(currency_pair: str, year_folder_path: str, zip_file_path: str) -> None:
        os.remove(zip_file_path)
        shutil.rmtree(os.path.join(year_folder_path, '__MACOSX'), ignore_errors=True)

        if currency_pair in os.listdir(year_folder_path):
            # In 2018 and previous years, zips come with a subfolder of the
            currency_subfolder_path = os.path.join(year_folder_path, currency_pair)
            subfolder_files = os.listdir(currency_subfolder_path)

            for subfolder_file in subfolder_files:
                if os.path.isfile(os.path.join(year_folder_path, subfolder_file)):
                    os.remove(os.path.join(year_folder_path, subfolder_file))
                shutil.move(os.path.join(currency_subfolder_path, subfolder_file), year_folder_path)
            os.rmdir(currency_subfolder_path)

    def _download_and_unzip_files(self, year: str, currency_pair: str) -> None:
        url = config.SOURCES[self._market].format(year, currency_pair)
        response = requests.get(url, stream=True, timeout=config.CONECTION_TIMEOUT)
        response_code = response.status_code

        year_folder_path = os.path.join(config.DATA_FOLDER_PATH, self._market, currency_pair, year)
        if response_code == 200:
            filename = f'{currency_pair}_{year}.zip'
            zip_file_path = os.path.join(config.DATA_FOLDER_PATH, self._market, currency_pair, year, filename)

            with open(zip_file_path, 'wb') as zip_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        zip_file.write(chunk)

            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(year_folder_path)

            ExtractForex.clean_directories(currency_pair, year_folder_path, zip_file_path)

        elif response_code == 404:
            raise ResourceNotFoundException("The next resource doesn't exist. Please check if the URL is malformed or "
                                            f"if the resource is inexistent.\n\t{url}")
        else:
            raise Exception()

    @staticmethod
    def get_column_names(df: pd.DataFrame, currency: str, year: str) -> List[str]:
        """ This method checks if the columns are in the order that they are expected """
        df.columns = ['date', 'hour', 'col1', 'col2', 'col3', 'col4', 'vol']
        data_rows = df.shape[0]

        max_column_rows = df.query('col2 >= col1 and col2 >= col3 and col2 >= col4').shape[0]

        if data_rows != max_column_rows:
            raise ColumnNamesMisinterpreted(f"MAX column is not the expected one, please check the dataframe. Happened for currency {currency} and year {year}")

        min_column_rows = df.query('col3 <= col1 and col3 <= col2 and col3 <= col4').shape[0]

        if data_rows != min_column_rows:
            raise ColumnNamesMisinterpreted(f"MIN column is not the expected one, please check the dataframe. Happened for currency {currency} and year {year} ")

        # TODO: Check how to validate open and close columns. In most of the cases, the col1 price is the col4 price of the previous row, but this does not happen always

        # df['col4_shifted'] = df['col4'].shift(1)
        # open_close_rows = df.query('col1==col4_shifted').shape[0] + 1  # First record is Nan

        # if data_rows != open_close_rows:
        #     raise ColumnNamesMisinterpreted(f"OPEN and CLOSE columns are not the expected ones, please check the dataframe. Happened for currency {currency} and year {year}")

        # df.drop(['col4_shifted'], axis=1, inplace=True)
        return ['date', 'hour', 'open', 'high', 'low', 'close', 'volume']

    @staticmethod
    def check_or_create_all_file(year_path: str) -> None:
        """ Checks if the merged file that comes for closed years is in the extracted file. If it is not there, this method creates it. """
        file_list = os.listdir(year_path)
        all_files = [file for file in file_list if 'all.csv' in file]
        if len(all_files) == 0:
            year_df = pd.DataFrame()
            for file in file_list:
                df = pd.read_csv(os.path.join(year_path, file), header=None)
                year_df = pd.concat([year_df, df], axis=0, ignore_index=True)
            filename = file.split('_')[0] + '_' + file.split('_')[1] + '_all.csv'
            year_df.to_csv(os.path.join(year_path, filename), index=False, header=False)

    def _merge_data(self) -> None:
        full_df = pd.DataFrame()
        self._logger.info(f'Merging {self._market} data...')
        for currency in self._assets:
            currency_path = os.path.join(config.DATA_FOLDER_PATH, self._market, currency)
            for year in os.listdir(currency_path):
                year_path = os.path.join(currency_path, year)
                ExtractForex.check_or_create_all_file(year_path)

                year_files = os.listdir(year_path)
                complete_file = [os.path.join(year_path, file) for file in year_files if 'all.csv' in file][0]

                df_aux = pd.read_csv(complete_file, header=None)
                df_aux.dropna(subset=[2, 3, 4, 5], how='all', axis=0, inplace=True)  # equivalent columns to open, close, high, low (order is checked in the next line method call)
                df_aux.columns = ExtractForex.get_column_names(df_aux, currency, year)
                df_aux = df_aux[['date', 'hour', 'open', 'close', 'high', 'low', 'volume']]  # Column reordering
                df_aux['asset'] = currency

                full_df = pd.concat([full_df, df_aux], axis=0, ignore_index=True)

        full_df['date'] = pd.to_datetime(full_df['date'] + ' ' + full_df['hour'])
        full_df['market'] = self._market
        full_df.drop(['hour'], axis=1, inplace=True)
        full_df.to_parquet(os.path.join(config.DATA_FOLDER_PATH, self._market, 'merged', f'{self._market}.parquet'), engine='pyarrow', index=False)

    def run(self) -> None:
        self._extract_data()
        self._merge_data()


if __name__ == '__main__':
    ExtractForex().run()

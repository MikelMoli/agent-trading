import os
import sys
sys.path.append(os.path.join(os.getcwd()))

from time import sleep

import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

import config
from datetime import datetime
import zipfile


class ExtractForex:
    # base url has to be formatted with a valid currency pair. Check VALID_CURRENCY_PAIRS in config.py
    BASE_URL = 'https://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/{}'

    def __init__(self, currency: str, years_to_extract: int = None):
        self._currency = currency
        self._currency_url = config.SOURCES["FOREX"].format(self._currency)
        today = datetime.today()
        self._current_year = today.year
        self._current_month = today.month
        self._driver = self.get_driver()

        if years_to_extract is None:
            years_to_extract = config.YEARS_TO_EXTRACT
        self._years_to_extract = years_to_extract

    def get_driver(self):
        service = ChromeService(ChromeDriverManager().install())
        prefs = {"download.default_directory" : f"{os.path.join(os.getcwd(), 'data')}"}

        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("--browser.download.folderList=2")
        options.add_argument("--browser.download.manager.showWhenStarting=False")
        options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(service=service, options=options)

    def _download_zip_data(self):
        urls = self.get_url_list()
        cookies_accepted = False
        for url in urls:
            self._driver.get(url)
            if not cookies_accepted:
                cookies_accepted = True
                try:
                    self._driver.find_element(By.XPATH, '//*[@id="cookie_action_close_header"]').click()
                    self._driver.find_element(By.XPATH, '//*[@id="onesignal-slidedown-cancel-button"]').click()
                except NoSuchElementException:
                    print('No hay elemento')
                except ElementNotInteractableException:
                    print('No se puede hacer click en el elemento')

            elems = self._driver.find_elements(By.XPATH, '//*[@id="a_file"]')
            print('Downloaded:', url)
            if len(elems) > 1:
                print('Upsie')
            else:
                elems[0].click()
                sleep(2)
    
    def _fix_bad_zip_file(self, filepath):
        f = open(filepath, 'r+b')  
        data = f.read()  
        pos = data.find('\x50\x4b\x05\x06')
        if (pos > 0):  
            f.seek(pos + 22)
            f.truncate()  
            f.close()  
        else:
            raise Exception()
            # raise error, file is truncated  


    def _handle_bad_zip_files(self, filepath):
        parts = filepath.split(".")
        if parts[-1] != "zip":
            new_filepath = ""
            for part in parts[:-1]:
                if part == "zip":
                    new_filepath += f".{part}"
                else:
                    new_filepath += part
            os.rename(filepath, new_filepath)
            self._fix_bad_zip_file(new_filepath)

            return new_filepath
        else:
            return filepath

    def _extract_zips_into_folders(self):
        for file in os.listdir(config.DATA_FOLDER_PATH):
            if '.zip' in file:
                folder_name = file.split('M1')[1][0:4]
                folder = self.create_folder_if_not_exists(folder_name)
                filepath = f'{config.DATA_FOLDER_PATH}/{file}'
                filepath = self._handle_bad_zip_files(filepath)

                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(folder)
                    os.remove(filepath)

    def create_folder_if_not_exists(self, year: str):
        folder_path = f'{config.DATA_FOLDER_PATH}/{year}'
        if year not in os.listdir(os.path.join(os.getcwd(), 'data')):
            os.mkdir(folder_path)

        return folder_path

    def get_url_list(self):
        # https://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/eurusd/2023/4
        # https://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/eurusd/2022

        base_url = 'https://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/{}/{}'

        month_list = [*range(1, self._current_month+1)]
        year_list = [*range(self._current_year - self._years_to_extract, self._current_year)]  # There is no + 1 as the last year is the only one that uses months

        extraction_urls = [base_url.format(self._currency, f'{self._current_year}/{month}') for month in month_list]
        for year in year_list:
            extraction_urls.append(base_url.format(self._currency, year))

        return extraction_urls

    def _merge_data(self):
        final_folder_name = 'merged'
        merged_path = self.create_folder_if_not_exists(final_folder_name)
        folders = os.listdir(config.DATA_FOLDER_PATH)
        final_df = pd.DataFrame()

        for folder in folders:
            if folder != final_folder_name:
                folder_files = os.listdir(os.path.join(config.DATA_FOLDER_PATH, folder))
                for file in folder_files:
                    if '.csv' in file:
                        aux_df = pd.read_csv(os.path.join(config.DATA_FOLDER_PATH, folder, file), header=None)
                        aux_df.columns = ['date', 'hour', 'open', 'high', 'close', 'low', 'volume']
                        final_df = pd.concat([final_df, aux_df], axis=0, ignore_index=True)

        final_df.drop(['volume'], axis=1, inplace=True)  # Sólo hay 0s en la columna, no aporta nada
        final_df.to_csv(f'{merged_path}/merged_data.csv', index=False)

    def run(self):
        self._download_zip_data()
        self._extract_zips_into_folders()
        self._merge_data()


if __name__ == '__main__':
    exfor = ExtractForex(currency='EURUSD')
    exfor.run()
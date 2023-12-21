from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
import time
from urllib import parse

import requests


class MoexStrategy(ABC):
    '''Общий класс-стратегия работы с API Московской биржи'''

    _API_MOEX_URL = 'https://iss.moex.com'

    @abstractmethod
    def build_url(self, method_url: str, params: dict) -> str:
        '''Конструктор url путей запросов к API moex'''

        url_parts = list(parse.urlparse(self._API_MOEX_URL))
        url_parts[2] = method_url
        url_parts[4] = parse.urlencode(params)
        result_url = parse.urlunparse(url_parts)

        return result_url

    # @abstractmethod
    # def process_data(self):
    #     pass


class BondList(MoexStrategy):
    '''Класс-стратегия работы со списком облигаций Московской биржи'''

    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(__class__.__name__)

    def build_url(self, method_url: str, params: dict) -> str:
        '''Конструктор url путей запросов к получению списка
           облигаций одной страници
        '''

        return super().build_url(method_url=method_url, params=params)

    # def process_data(self):
    #     start_time = datetime.now()
    #     page = -1
    #     while True:
    #         page += 1
    #         return next(self.generator_bonds(page=page, start_time=start_time))

    def generator_bonds(self, page: int) -> list:
        '''Генерирование последовательности списка облигаций со всей биржи'''

        # Вывод информации о текущей странице
        self.log.info(f'Page {page + 1}')

        # Получение списка облигаций для текущей страницы
        list_bonds = self._get_list_bonds(page=page)

        # Если список пустой, завершаем генерацию
        if not list_bonds:
            return []

        yield list_bonds

    def _get_list_bonds(self, page: int = 0, limit: int = 100) -> list:
        '''Получение списка торгуемых облигаций по запросу'''

        method_url = '/iss/securities.json'
        start = page * limit
        params = {
            'iss.meta': 'off',
            'securities.columns': 'secid, is_traded',
            'engine': 'stock',
            'market': 'bonds',
            'start': start
        }

        list_bonds_url = self.build_url(method_url=method_url, params=params)
        raw_list_bonds = requests.get(list_bonds_url).json()

        return self._process_raw_bonds(raw_list_bonds)

    def _process_raw_bonds(self, raw_list_bonds: dict) -> list:
        '''Обработка необработанных данных облигаций'''

        securities_info = raw_list_bonds.get('securities')
        if not securities_info:
            return []

        columns = securities_info.get('columns')
        secid_index = columns.index('secid')
        is_traded_index = columns.index('is_traded')
        data = securities_info.get('data')

        return self._filter_traded_bonds(data, secid_index, is_traded_index)

    def _filter_traded_bonds(self,
                             data: list,
                             secid_index: int,
                             is_traded_index: int) -> list:
        '''Отбор списка торгуемых облигаций'''

        traded_bonds = [bond[secid_index] for bond in data
                        if bond[is_traded_index] == 1]
        return traded_bonds


class Bond(MoexStrategy):
    '''Класс-стратегия работы с облигацией Московской биржи'''

    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(__class__.__name__)

    def build_url(self, method_url: str, params: dict) -> str:
        '''Конструктор url путей запросов к получению информации по
           облигации
        '''

        return super().build_url(method_url=method_url, params=params)

    def process_data(self, secid):
        return self.get_detail_bond(secid=secid)

    def get_detail_bond(self, secid: str) -> dict:
        '''Получение общей детальной информации по облигации'''

        # Формирование URL для запроса информации об облигации
        method_url = f'/iss/securities/{secid}.json'
        params = {
            'iss.meta': 'off',
            'description.columns': 'name, title, value',
            'iss.only': 'description'
        }
        bond_url = self.build_url(method_url=method_url, params=params)

        try:
            # Запрос информации об облигации
            bond_response = requests.get(bond_url)
            bond_data = bond_response.json()

            # Извлечение необходимых данных из ответа
            description = bond_data.get('description')
            data = description.get('data')
            columns = description.get('columns')

            value_index = columns.index('value')
            name_index = columns.index('name')

            # Словарь с необходимыми ключами и требуемыми типами данных
            # для преобразования
            key_type = {
                'shortname': str,
                'secid': str,
                'isin': str,
                'matdate': self._parse_date,
                'initialfacevalue': int,
                'faceunit': str,
                'listlevel': int,
                'daystoredemption': int,
                'facevalue': float,
                'isqualifiedinvestors': int,
                'couponfrequency': int,
                'coupondate': self._parse_date,
                'couponpercent': float,
                'couponvalue': float,
                'highrisk': int,
                'group': str,
                'type': str}

            # Создание словаря с информацией об облигации с необходимыми
            #  ключами и не пустыми данными
            bond_info = {}
            for i in data:
                key_param = i[name_index].lower()
                value_param = i[value_index]
                type_param = key_type.get(key_param)

                if key_param in key_type.keys() and value_param:
                    bond_info[key_param] = type_param(value_param)

            # Проверка на квалификацию инвестора и частоту выплаты купона
            if bond_info.get('isqualifiedinvestors') == 1:
                return None

            return self.get_moex_yield(bond=bond_info)

        except requests.exceptions.RequestException as e:
            # Обработка ошибок при запросе
            self.log.info(f'Ошибка при получении сведений об облиг. для {secid}: {e}')
            return None
        except (KeyError, IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info(f'Ошибка при обработке сведений об облиг. для {secid}: {e}')
            return None

    def _parse_date(self, date_str):
        '''Функция для преобразования строковой даты в формате '%Y-%m-%d'
           в объект datetime.date
        '''
        return (datetime.strptime(date_str, '%Y-%m-%d').date()
                if date_str else None)

    def get_moex_yield(self, bond: dict) -> dict:
        '''Получение доходности, цены и НКД'''

        # Определение временного интервала для запроса истории доходности
        date_now = datetime.now()
        delta_date = date_now - timedelta(days=7)
        till_date = datetime.strftime(date_now, '%Y-%m-%d')
        from_date = datetime.strftime(delta_date, '%Y-%m-%d')

        secid = bond.get('secid')

        # Формирование URL для запроса истории доходности
        method_url = f'/iss/history/engines/stock/markets/bonds/yields/{secid}.json'
        params = {
            'iss.meta': 'off',
            'sort_order': 'desc',
            'from': from_date,
            'till': till_date,
            'limit': 1
        }

        bond_url = self.build_url(method_url=method_url, params=params)

        try:
            # Запрос истории доходности
            bond_price_response = requests.get(bond_url)
            bond_price_data = bond_price_response.json()

            # Извлечение данных о доходности
            history_yields = bond_price_data.get('history_yields')
            data = history_yields.get('data')[0]
            columns = history_yields.get('columns')

            # Выбор необходимых параметров
            # (цена, накопленный купон, эффективная доходность)
            price_params = ['price', 'accint', 'effectiveyield']
            bond_info = {param: data[columns.index(param.upper())]
                         for param in price_params}

            bond = bond | bond_info
            bond = bond_info | self._calc_bond(bond_info=bond)

            return bond

        except requests.exceptions.RequestException as e:
            # Обработка ошибок при запросе
            self.log.info(f'Ошибка при получении доходности MOEX для {secid}: {e}')
            return {}
        except (IndexError, TypeError) as e:
            # Обработка ошибок при обработке данных
            # self.log.info(f'Ошибка обработки доходности MOEX для {secid}: {e}')
            return {}

    def _calc_bond(self,
                   bond_info: dict,
                   commission: float = 0.3,
                   tax: int = 13) -> dict:
        '''Калькуляция реальной годовой доходности'''

        year = 365

        # Извлечение необходимых данных из информации об облигации
        price = bond_info.get('price')
        accint = bond_info.get('accint')
        face_value = bond_info.get('facevalue')
        coupon_frequency = bond_info.get('couponfrequency')
        days_to_redemption = bond_info.get('daystoredemption')
        coupon_value = bond_info.get('couponvalue')

        # Расчет цены покупки
        buy_price = face_value * price / 100 + accint
        commission_buy = buy_price * commission / 100
        final_price = buy_price + commission_buy

        # Расчет налога при продаже
        sold_delta = face_value - final_price
        sold_tax = max(0, sold_delta * tax / 100)

        # Расчет купонного дохода и налога на купоны
        coupon_day = year // coupon_frequency
        coupon_num = days_to_redemption // coupon_day + 1
        coupon_sum = coupon_num * coupon_value
        coupon_tax = coupon_sum * tax / 100

        # Расчет общего дохода и процента годовой доходности
        income = (sold_delta + coupon_sum) - (sold_tax + coupon_tax)
        profit = income / final_price * 100
        day_percent = profit / days_to_redemption
        year_percent = round(day_percent * year, 2)

        # Добавление информации о годовой доходности в информацию об облигации
        bond_info = bond_info | {'year_percent': year_percent}

        return bond_info


class MoexClient:
    def __init__(self, strategy):
        self.strategy = strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def execute_request(self, **kwargs):
        return self.strategy.process_data(**kwargs)

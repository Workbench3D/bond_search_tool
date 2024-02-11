from abc import ABC, abstractmethod
from datetime import datetime
import logging
import requests

from schemas import bond as schema


class MoexStrategy(ABC):
    '''Общий интерфейс работы с API Московской биржи'''

    _API_MOEX_URL: str = 'https://iss.moex.com'

    @abstractmethod
    def process_data(self):
        '''Метод для обработки данных, должен быть реализован в подклассах.'''
        raise NotImplementedError


class BondList(MoexStrategy):
    '''Класс-стратегия работы со списком облигаций Московской биржи'''

    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(__class__.__name__)
        self.session = requests.Session()

    def process_data(self, page: int) -> list:
        '''Обработка данных для заданной страницы'''
        return next(self._generator_bonds(page=page))

    def _generator_bonds(self, page: int) -> list:
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
            'securities.columns': 'secid',
            'engine': 'stock',
            'market': 'bonds',
            'is_trading': 1,
            'start': start
        }

        url = f'{self._API_MOEX_URL}{method_url}'
        response = self.session.get(url=url, params=params).json()
        securities = schema.BondListModel.model_validate(response).securities
        traded_bonds = [bond[0] for bond in securities.data]

        return traded_bonds


class Bond(MoexStrategy):
    '''Класс-стратегия работы с облигацией Московской биржи'''

    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        self.log = logging.getLogger(__class__.__name__)
        self.session = requests.Session()

    def process_data(self, secid: str) -> dict | None:
        '''Обработка данных для заданной облигации'''
        dump = self._map_values(secid=secid)
        if dump is not None:
            return dump.model_dump()
        return None

    def _map_values(self, secid: str) -> schema.BondModel | None:
        '''Отображение значений для заданной облигации'''
        bond_info = self._get_detail_bond(secid=secid)
        if bond_info is None:
            return None
        moex_yield = self._get_moex_yield(secid=secid)
        coupons = self._get_amortization(secid=secid)

        price = moex_yield.last_price
        if moex_yield.last_price == 0:
            price = moex_yield.last_day_price
        accint = moex_yield.accint
        face_value = bond_info.face_value
        days_to_redemption = bond_info.days_to_redemption
        sum_coupon = coupons.sum_coupon

        year_percent = self._calc_bond(price=price,
                                       accint=accint,
                                       face_value=face_value,
                                       days_to_redemption=days_to_redemption,
                                       sum_coupon=sum_coupon)

        bond_data = {'shortname': bond_info.short_name,
                     'secid': bond_info.secid,
                     'matdate': bond_info.matdate,
                     'face_unit': bond_info.face_unit,
                     'list_level': bond_info.list_level,
                     'days_to_redemption': days_to_redemption,
                     'face_value': face_value,
                     'coupon_frequency': bond_info.coupon_frequency,
                     'coupon_date': bond_info.coupon_date,
                     'coupon_percent': bond_info.coupon_percent,
                     'coupon_value': bond_info.coupon_value,
                     'highrisk': bond_info.high_risk,
                     'type': bond_info.type,
                     'accint': accint,
                     'price': price,
                     'moex_yield': moex_yield.moex_yield,
                     'amortizations': coupons.amortizations,
                     'floater': coupons.floater,
                     'sum_coupon': sum_coupon,
                     'year_percent': year_percent}

        bond_data = schema.BondModel.model_validate(bond_data)

        return bond_data

    def _get_detail_bond(self, secid: str) -> schema.PrimaryDataModel | None:
        '''Получение общей детальной информации по облигации'''

        # Формирование URL для запроса информации об облигации
        method_url = f'/iss/securities/{secid}.json'
        params = {
            'iss.meta': 'off',
            'description.columns': 'name, value',
            'iss.only': 'description'
        }

        try:
            # Запрос информации об облигации
            url = f'{self._API_MOEX_URL}{method_url}'
            response = self.session.get(url=url, params=params).json()

            response = schema.PrimaryRequestModel.model_validate(response)
            desc = response.description
            desc = {i[0]: i[1] for i in desc.data}
            bond_info = schema.PrimaryDataModel.model_validate(desc)

            # Проверка на квалификацию инвестора и дней до погашения
            if (bond_info.is_qualified_investors == 1
                    or bond_info.days_to_redemption < 1):
                return None

            return bond_info

        except requests.exceptions.RequestException as e:
            # Обработка ошибок при запросе
            self.log.info(
                f'Ошибка при получении сведений об облиг. для {secid}: {e}')
            return None
        except (KeyError, IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info(
                f'Ошибка при обработке сведений об облиг. для {secid}: {e}')
            return None

    def _get_moex_yield(self, secid: str) -> schema.YieldDataModel | None:
        '''Получение доходности, цены и НКД'''

        # Формирование URL для запроса истории доходности
        raw_url = '/iss/engines/stock/markets/bonds/securities/'
        method_url = f'{raw_url}{secid}.json'
        params = {
            'iss.meta': 'off',
            'iss.only': 'securities, marketdata',
            'marketdata.columns': 'LAST, MARKETPRICE, YIELD',
            'securities.columns': 'ACCRUEDINT',
            'marketprice_board': 1
        }

        try:
            # Запрос истории доходности
            url = f'{self._API_MOEX_URL}{method_url}'
            response = self.session.get(url=url, params=params).json()

            response_model = schema.YieldRequestModel.model_validate(response)

            securities = response_model.securities
            securities = {securities.columns[0]: securities.data[0][0]}

            marketdata = response_model.marketdata
            marketdata = {
                marketdata.columns[i]: marketdata.data[0][i]
                for i in range(len(marketdata.columns))}

            moex_yield = securities | marketdata
            moex_yield = schema.YieldDataModel.model_validate(moex_yield)

            return moex_yield

        except requests.exceptions.RequestException as e:
            # Обработка ошибок при запросе
            self.log.info(
                f'Ошибка при получении доходности MOEX для {secid}: {e}')
            return None
        except (IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info(
                f'Ошибка при MOEX для {secid}: {e}')
            return None

    def _get_amortization(self, secid: str) -> schema.CouponDataModel:
        '''Получение значений амортизации, плавающего купона и суммы купонов'''

        date_now = datetime.now()
        method_url = f'/iss/securities/{secid}/bondization.json'
        params = {
            'iss.meta': 'off',
            'iss.only': 'amortizations,coupons',
            'amortizations.columns': 'facevalue',
            'coupons.columns': 'coupondate, value',
            'limit': 'unlimited'
        }
        url = f'{self._API_MOEX_URL}{method_url}'
        response = self.session.get(url=url, params=params).json()

        coupon_dict = schema.CouponRequestModel.model_validate(response)

        amortizations = len(coupon_dict.amortizations.data) > 1

        sum_coupon = 0
        floater = False
        date_now = datetime.now()
        coupons = coupon_dict.coupons
        coupons = {datetime.strptime(i[0], '%Y-%m-%d'): i[1]
                   for i in coupons.data}
        for key, value in coupons.items():
            delta = key - date_now
            if delta.days > 0:
                coupon = float(value) if value is not None else 0
                floater = coupon is None
                sum_coupon += coupon
        sum_coupon = round(sum_coupon, 2)

        coupons = {'amortizations': amortizations,
                   'floater': floater,
                   'sum_coupon': sum_coupon}

        coupons = schema.CouponDataModel.model_validate(coupons)

        return coupons

    def _calc_bond(self,
                   price: float,
                   accint: float,
                   face_value: float,
                   days_to_redemption: int,
                   sum_coupon: float,
                   commission: float = 0.3,
                   tax: int = 13) -> float:
        '''Калькуляция реальной годовой доходности'''

        year = 365

        # Расчет цены покупки
        if price == 0:
            year_percent = 0
            return year_percent
        buy_price = face_value * price / 100 + accint
        commission_buy = buy_price * commission / 100
        final_price = buy_price + commission_buy

        # Расчет налога при продаже
        sold_delta = face_value - final_price
        sold_tax = max(0, sold_delta * tax / 100)

        # Расчет купонного дохода и налога на купоны
        coupon_tax = sum_coupon * tax / 100

        # Расчет общего дохода и процента годовой доходности
        income = (sold_delta + sum_coupon) - (sold_tax + coupon_tax)
        profit = income / final_price * 100
        day_percent = profit / days_to_redemption
        year_percent = round(day_percent * year, 2)

        return year_percent


class ContextStrategy:
    '''Контекст работает с выбором стратегий и их выполнением'''

    def __init__(self, strategy):
        self.strategy = strategy

    def set_strategy(self, strategy):
        '''Установка стратегии'''
        self.strategy = strategy

    def execute_strategy(self, **kwargs):
        '''Выполнение стратегии с передачей аргументов'''
        return self.strategy.process_data(**kwargs)

from abc import ABC, abstractmethod
from datetime import datetime
from time import time
import logging
import aiohttp

from schemas import bond as schema


class MoexStrategy(ABC):
    """Общий интерфейс работы с API Московской биржи"""

    _API_MOEX_URL: str = "https://iss.moex.com"

    @abstractmethod
    async def process_data(self):
        """Метод для обработки данных, должен быть реализован в подклассах."""
        raise NotImplementedError


class BondList(MoexStrategy):
    """Класс-стратегия работы со списком облигаций Московской биржи"""

    def __init__(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.log = logging.getLogger(__class__.__name__)

    async def process_data(self):
        """Обработка данных для заданной страницы"""
        try:
            async with aiohttp.ClientSession(trust_env=True) as session:
                method_url = "/iss/securities.json"
                url = f"{self._API_MOEX_URL}{method_url}"
                page = 0
                model_response = schema.BondListModel
                while True:
                    # Вывод информации о текущей странице
                    self.log.info(f"Страница {page + 1}")

                    start = 100 * page
                    params = {
                        "iss.meta": "off",
                        "securities.columns": "secid",
                        "engine": "stock",
                        "market": "bonds",
                        "is_trading": 1,
                        "start": start,
                    }
                    page += 1
                    async with session.get(url=url, params=params) as response:
                        response_bonds = await response.json()
                        response = model_response.model_validate(response_bonds)
                        bond_list = response.securities.data

                        # Если список пустой, завершаем генерацию
                        if not bond_list:
                            return
                        result = [i[0] for i in bond_list]
                        yield result

        except aiohttp.ClientError as e:
            # Обработка ошибок при запросе
            self.log.info(
                f"Ошибка при запросе сведений об списке облиг. для страницы {page + 1}: {e}"
            )
            yield []


class Bond(MoexStrategy):
    """Класс-стратегия работы с облигацией Московской биржи"""

    def __init__(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.log = logging.getLogger(__class__.__name__)

    async def process_data(self, list_bond: list) -> list:
        result = []
        async with aiohttp.ClientSession(trust_env=True) as session:
            for secid in list_bond:
                bond_info = await self._get_detail_bond(session=session, secid=secid)
                moex_yield = await self._get_moex_yield(session=session, secid=secid)
                coupons = await self._get_amortization(session=session, secid=secid)
                if not bond_info or not moex_yield or not coupons:
                    continue

                price = moex_yield.price
                accint = moex_yield.accint
                face_value = bond_info.face_value
                days_to_redemption = bond_info.days_to_redemption
                sum_coupon = coupons.sum_coupon
                if price == 0 or days_to_redemption == 0:
                    continue

                year_percent = await self._calc_bond(
                    price=price,
                    accint=accint,
                    face_value=face_value,
                    days_to_redemption=days_to_redemption,
                    sum_coupon=sum_coupon,
                )

                bond_data = {
                    "shortname": bond_info.short_name,
                    "secid": bond_info.secid,
                    "matdate": bond_info.matdate,
                    "face_unit": bond_info.face_unit,
                    "list_level": bond_info.list_level,
                    "days_to_redemption": days_to_redemption,
                    "face_value": face_value,
                    "is_qualified_investors": bond_info.is_qualified_investors,
                    "coupon_frequency": bond_info.coupon_frequency,
                    "coupon_date": bond_info.coupon_date,
                    "coupon_percent": bond_info.coupon_percent,
                    "coupon_value": bond_info.coupon_value,
                    "highrisk": bond_info.high_risk,
                    "type": bond_info.type,
                    "accint": accint,
                    "price": price,
                    "moex_yield": moex_yield.moex_yield,
                    "amortizations": coupons.amortizations,
                    "floater": coupons.floater,
                    "sum_coupon": sum_coupon,
                    "year_percent": year_percent,
                }

                bond_data = schema.BondModel.model_validate(bond_data)
                bond_data = bond_data.model_dump()
                result.append(bond_data)

        return result

    async def _get_detail_bond(
        self, session: aiohttp.ClientSession, secid: str
    ) -> schema.PrimaryDataModel | None:
        """Получение общей детальной информации по облигации"""

        model_response = schema.PrimaryRequestModel
        model_data = schema.PrimaryDataModel
        # Формирование URL для запроса информации об облигации
        method_url = f"/iss/securities/{secid}"
        params = {
            "iss.meta": "off",
            "description.columns": "name, value",
            "iss.only": "description",
        }

        try:
            # Запрос информации об облигации
            url = f"{self._API_MOEX_URL}{method_url}.json"
            async with session.get(url=url, params=params) as response:
                response_bond = await response.json()
                response = model_response.model_validate(response_bond)
                desc = response.description
                desc = {i[0]: i[1] for i in desc.data}
                bond_info = model_data.model_validate(desc)

                # Проверка на квалификацию инвестора
                if bond_info.is_qualified_investors == 1:
                    return None

                return bond_info

        except aiohttp.ClientError as e:
            # Обработка ошибок при запросе
            self.log.info(f"Ошибка при запросе сведений об облиг. для {secid}: {e}")
            return None
        except (KeyError, IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info(f"Ошибка при обработке сведений облиг. для {secid}: {e}")
            return None

    async def _get_moex_yield(
        self, session: aiohttp.ClientSession, secid: str
    ) -> schema.YieldDataModel | None:
        """Получение доходности, цены и НКД"""

        model_response = schema.YieldRequestModel
        raw_model_data = schema.YieldRawDataModel
        model_data = schema.YieldDataModel

        # Формирование URL для запроса истории доходности
        method_url = f"/iss/engines/stock/markets/bonds/securities/{secid}"
        params = {
            "iss.meta": "off",
            "iss.only": "securities, marketdata",
            "marketdata.columns": "LAST, MARKETPRICE, YIELD",
            "securities.columns": "ACCRUEDINT",
            "marketprice_board": 1,
        }

        try:
            # Запрос истории доходности
            url = f"{self._API_MOEX_URL}{method_url}.json"
            async with session.get(url=url, params=params) as response:
                response_bond = await response.json()
                response = model_response.model_validate(response_bond)

                securities = response.securities
                securities = {securities.columns[0]: securities.data[0][0]}

                marketdata = response.marketdata
                marketdata = {
                    marketdata.columns[i]: marketdata.data[0][i]
                    for i in range(len(marketdata.columns))
                }

                raw_yield = securities | marketdata
                raw_yield = raw_model_data.model_validate(raw_yield)
                price = raw_yield.last_price
                if raw_yield.last_price == 0 and raw_yield.marketprice != 0:
                    price = raw_yield.marketprice
                moex_yield = {
                    "accint": raw_yield.accint,
                    "price": price,
                    "moex_yield": raw_yield.moex_yield,
                }

                moex_yield = model_data.model_validate(moex_yield)

                return moex_yield

        except aiohttp.ClientError as e:
            # Обработка ошибок при запросе
            self.log.info(f"Ошибка при запросе доходности MOEX для {secid}: {e}")
            return None
        except (IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info(f"Ошибка при обработке доходности MOEX для {secid}: {e}")
            return None

    async def _get_amortization(
        self, session: aiohttp.ClientSession, secid: str
    ) -> schema.CouponDataModel | None:
        """Получение значений амортизации, плавающего купона и суммы купонов"""

        model_response = schema.CouponRequestModel
        model_data = schema.CouponDataModel

        date_now = datetime.now()
        method_url = f"/iss/securities/{secid}/bondization"
        params = {
            "iss.meta": "off",
            "iss.only": "amortizations,coupons",
            "amortizations.columns": "facevalue",
            "coupons.columns": "coupondate, value",
            "limit": "unlimited",
        }
        try:
            url = f"{self._API_MOEX_URL}{method_url}.json"
            async with session.get(url=url, params=params) as response:
                response_bond = await response.json()

                response = model_response.model_validate(response_bond)

                amortizations = len(response.amortizations.data) > 1

                sum_coupon = 0
                floater = False
                coupons = response.coupons
                coupons = {
                    datetime.strptime(i[0], "%Y-%m-%d"): i[1] for i in coupons.data
                }
                for key, value in coupons.items():
                    delta = key - date_now
                    if delta.days > 0:
                        coupon = value
                        if coupon is None:
                            floater = True
                            coupon = 0
                        sum_coupon += coupon
                sum_coupon = round(sum_coupon, 2)

                coupons = {
                    "amortizations": amortizations,
                    "floater": floater,
                    "sum_coupon": sum_coupon,
                }

                coupons = model_data.model_validate(coupons)

                return coupons
        except aiohttp.ClientError as e:
            # Обработка ошибок при запросе
            self.log.info(f"Ошибка при запросе купонов MOEX для {secid}: {e}")
            return None
        except (IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info(f"Ошибка при обработке купонов MOEX для {secid}: {e}")
            return None

    async def _calc_bond(
        self,
        price: float,
        accint: float,
        face_value: float,
        days_to_redemption: int,
        sum_coupon: float,
        commission: float = 0.3,
        tax: int = 13,
    ) -> float:
        """Калькуляция реальной годовой доходности"""

        year = 365

        # Расчет цены покупки
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
    """Контекст работает с выполнением стратегий"""

    def __init__(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.log = logging.getLogger(__class__.__name__)

    async def execute_strategy(self, update_data):
        start = time()
        bond_list = BondList()
        bond = Bond()
        async for i in bond_list.process_data():
            bonds = await bond.process_data(list_bond=i)
            update_data(bonds=bonds)

        time_result = round((time() - start), 2)
        self.log.info(f"Время выполнения - {time_result}")

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
from time import time
import logging
from aiohttp import ClientSession, ClientError

from schemas.bond import (
    BondListModel,
    BondModel,
    PrimaryDataModel,
    PrimaryRequestModel,
    YieldDataModel,
    YieldRawDataModel,
    YieldRequestModel,
    CouponDataModel,
    CouponRequestModel,
)


class MoexStrategy(ABC):
    """Общий интерфейс работы с API Московской биржи"""

    _API_MOEX_URL: str = "https://iss.moex.com"
    headers = {"Accept-Encoding": "gzip"}

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
            async with ClientSession(trust_env=True, headers=self.headers) as session:
                method_url = "/iss/securities.json"
                url = f"{self._API_MOEX_URL}{method_url}"
                page = 0
                while True:
                    # Вывод информации о текущей странице
                    self.log.info("Страница %d", page + 1)

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
                        response = BondListModel.model_validate(response_bonds)
                        bond_list = response.securities.data

                        # Если список пустой, завершаем генерацию
                        if not bond_list:
                            return
                        result = [i[0] for i in bond_list]
                        yield result

        except ClientError as e:
            # Обработка ошибок при запросе
            self.log.info(
                "Ошибка при запросе сведений об списке облиг. для страницы %d: %s",
                page + 1,
                e,
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
        async with ClientSession(trust_env=True, headers=self.headers) as session:
            for secid in list_bond:
                bond_info = await self._get_detail_bond(session=session, secid=secid)
                moex_yield = await self._get_moex_yield(session=session, secid=secid)
                if not bond_info or not moex_yield:
                    continue

                coupons = await self._get_amortization(
                    session=session,
                    secid=secid,
                    coupon_frequency=bond_info.coupon_frequency,
                )
                if not bond_info or not moex_yield or not coupons:
                    continue

                price = moex_yield.price
                face_value = bond_info.face_value
                days_to_redemption = bond_info.days_to_redemption
                sum_coupon = coupons.sum_coupon
                sum_coupon_percent = coupons.sum_coupon_percent
                if price == 0 or days_to_redemption == 0:
                    continue

                # Расчет НКД самостоятельно на основе дат купонов
                accint, accint_percent = self._calc_accint(
                    coupons=coupons.coupons,
                    face_value=face_value,
                )

                # self.log.info("[%s] Расчет доходности:", secid)
                # self.log.info(
                #     "  price=%s, accint=%s, accint_percent=%s", price, accint, accint_percent
                # )
                # self.log.info(
                #     "  face_value=%s, days_to_redemption=%s", face_value, days_to_redemption
                # )
                # self.log.info(
                #     "  sum_coupon=%s, sum_coupon_percent=%s", sum_coupon, sum_coupon_percent
                # )

                year_percent = await self._calc_bond(
                    price=price,
                    accint=accint_percent,
                    days_to_redemption=days_to_redemption,
                    sum_coupon_percent=sum_coupon_percent,
                )

                # self.log.info("[%s] Итоговая доходность: %s%%", secid, year_percent)

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
                    "accint_percent": accint_percent,
                    "price": price,
                    "moex_yield": moex_yield.moex_yield,
                    "amortizations": coupons.amortizations,
                    "floater": coupons.floater,
                    "sum_coupon": sum_coupon,
                    "sum_coupon_percent": sum_coupon_percent,
                    "year_percent": year_percent,
                }

                bond_data = BondModel.model_validate(bond_data)
                bond_data = bond_data.model_dump()
                result.append(bond_data)

        return result

    async def _get_detail_bond(
        self, session: ClientSession, secid: str
    ) -> PrimaryDataModel | None:
        """Получение общей детальной информации по облигации"""

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
            async with session.get(
                url=url, params=params, headers=self.headers
            ) as response:
                response_bond = await response.json()
                response = PrimaryRequestModel.model_validate(response_bond)
                desc = response.description
                desc = {key: value for key, value in desc.data}
                bond_info = PrimaryDataModel.model_validate(desc)

                # Проверка на квалификацию инвестора
                if bond_info.is_qualified_investors == 1:
                    return None

                return bond_info

        except ClientError as e:
            # Обработка ошибок при запросе
            self.log.info("Ошибка при запросе сведений об облиг. для %s: %s", secid, e)
            return None
        except (KeyError, IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info("Ошибка при обработке сведений облиг. для %s: %s", secid, e)
            return None

    async def _get_moex_yield(
        self, session: ClientSession, secid: str
    ) -> YieldDataModel | None:
        """Получение доходности и цены"""

        # Формирование URL для запроса истории доходности
        method_url = f"/iss/engines/stock/markets/bonds/securities/{secid}"
        params = {
            "iss.meta": "off",
            "iss.only": "securities, marketdata",
            "marketdata.columns": "LAST, MARKETPRICE, YIELD",
            "marketprice_board": 1,
        }

        try:
            # Запрос истории доходности
            url = f"{self._API_MOEX_URL}{method_url}.json"
            async with session.get(
                url=url, params=params, headers=self.headers
            ) as response:
                response_bond = await response.json()
                response = YieldRequestModel.model_validate(response_bond)

                securities = response.securities
                securities = dict(zip(securities.columns, securities.data[0]))

                marketdata = response.marketdata
                marketdata = dict(zip(marketdata.columns, marketdata.data[0]))

                raw_yield = securities | marketdata
                raw_yield = YieldRawDataModel.model_validate(raw_yield)
                price = raw_yield.last_price
                if raw_yield.last_price == 0 and raw_yield.marketprice != 0:
                    price = raw_yield.marketprice
                moex_yield = {
                    "price": price,
                    "moex_yield": raw_yield.moex_yield,
                }

                moex_yield = YieldDataModel.model_validate(moex_yield)

                return moex_yield

        except ClientError as e:
            # Обработка ошибок при запросе
            self.log.info("Ошибка при запросе доходности MOEX для %s: %s", secid, e)
            return None
        except (IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info("Ошибка при обработке доходности MOEX для %s: %s", secid, e)
            return None

    async def _get_amortization(
        self,
        session: ClientSession,
        secid: str,
        coupon_frequency: int,
    ) -> CouponDataModel | None:
        """Получение значений амортизации, плавающего купона и суммы купонов"""

        date_now = datetime.now()
        method_url = f"/iss/securities/{secid}/bondization"
        params = {
            "iss.meta": "off",
            "iss.only": "amortizations,coupons",
            "amortizations.columns": "facevalue",
            "coupons.columns": "coupondate, value, valueprc",
            "limit": "unlimited",
        }
        try:
            url = f"{self._API_MOEX_URL}{method_url}.json"
            async with session.get(
                url=url, params=params, headers=self.headers
            ) as response:
                response_bond = await response.json()

                response = CouponRequestModel.model_validate(response_bond)

                amortizations = len(response.amortizations.data) > 1

                sum_coupon = 0
                sum_coupon_percent = 0
                floater = False
                coupons = response.coupons
                # coupons.data - это список [coupondate, value, valueprc]
                # valueprc - это годовой процент купона
                # Сохраняем все купоны для расчета НКД
                coupons_list: list[tuple[date, float, float]] = []

                # self.log.info("[%s] Купонов найдено: %d", secid, len(coupons.data))
                # self.log.info("[%s] Частота выплат: %d", secid, coupon_frequency)

                coupons_data = {
                    datetime.strptime(item[0], "%Y-%m-%d").date(): (item[1], item[2])
                    for item in coupons.data
                }
                for coupon_date, (
                    coupon_value,
                    coupon_rate_year,
                ) in coupons_data.items():
                    # Расчет процента за один купон: годовой процент / частоту выплат
                    coupon_percent = (
                        coupon_rate_year / coupon_frequency
                        if coupon_frequency > 0
                        else 0
                    )

                    # Сохраняем данные о купоне для расчета НКД
                    coupons_list.append((coupon_date, coupon_value, coupon_rate_year))

                    delta = coupon_date - date_now.date()
                    if delta.days > 0:
                        # self.log.info(
                        #     "[%s] Купон %s: value=%s, rate_year=%s%%, coupon_percent=%.4f%%",
                        #     secid, coupon_date, coupon_value, coupon_rate_year, coupon_percent
                        # )

                        if coupon_value is None:
                            floater = True
                            coupon_value = 0
                            coupon_percent = 0

                        sum_coupon += coupon_value
                        sum_coupon_percent += coupon_percent

                # self.log.info(
                #     "[%s] Сумма купонов: валюта=%s, процент=%.4f",
                #     secid, sum_coupon, sum_coupon_percent
                # )
                sum_coupon = round(sum_coupon, 2)
                sum_coupon_percent = round(sum_coupon_percent, 2)

                coupons_data_model = {
                    "amortizations": amortizations,
                    "floater": floater,
                    "sum_coupon": sum_coupon,
                    "sum_coupon_percent": sum_coupon_percent,
                    "coupons": coupons_list,
                }

                coupons = CouponDataModel.model_validate(coupons_data_model)

                return coupons
        except ClientError as e:
            # Обработка ошибок при запросе
            self.log.info("Ошибка при запросе купонов MOEX для %s: %s", secid, e)
            return None
        except (IndexError, TypeError, ValueError) as e:
            # Обработка ошибок при обработке данных
            self.log.info("Ошибка при обработке купонов MOEX для %s: %s", secid, e)
            return None

    def _calc_accint(
        self,
        coupons: list[tuple[date, float, float]],
        face_value: float,
    ) -> tuple[float, float]:
        """
        Расчет НКД в валюте и в процентах от номинала.

        Возвращает: (accint_value, accint_percent)
        """
        today = datetime.now().date()

        # Фильтруем будущие купоны
        future_coupons = [(d, v, r) for d, v, r in coupons if d > today]

        if not future_coupons:
            # self.log.info("  [accint] Нет будущих купонов, НКД = 0")
            return 0.0, 0.0

        # Находим последний прошедший и следующий купоны
        all_coupons_sorted = sorted(coupons, key=lambda x: x[0])

        last_coupon_date = None
        next_coupon_date = None
        next_coupon_value = None

        for i, (coupon_date, coupon_value, _) in enumerate(all_coupons_sorted):
            if coupon_date > today:
                next_coupon_date = coupon_date
                next_coupon_value = coupon_value
                if i > 0:
                    last_coupon_date = all_coupons_sorted[i - 1][0]
                break

        # Если нет предыдущего купона, используем дату выпуска (упрощенно)
        if last_coupon_date is None:
            # Берем предыдущую дату от следующего купона на основе частоты
            # Упрощенно: отнимаем ~6 месяцев для полугодовых купонов
            last_coupon_date = next_coupon_date - timedelta(days=182)

        if next_coupon_date is None or next_coupon_value is None:
            # self.log.info("  [accint] Не удалось найти следующий купон, НКД = 0")
            return 0.0, 0.0

        # Расчет дней
        days_in_period = (next_coupon_date - last_coupon_date).days
        days_accrued = (today - last_coupon_date).days

        if days_in_period <= 0:
            # self.log.info("  [accint] Ошибка расчета дней, НКД = 0")
            return 0.0, 0.0

        # НКД не может быть больше суммы купона
        days_accrued = min(days_accrued, days_in_period)

        # Расчет НКД пропорционально дням
        accint_value = next_coupon_value * (days_accrued / days_in_period)
        accint_percent = (accint_value / face_value) * 100 if face_value > 0 else 0

        # self.log.info("  [accint] last_coupon=%s, next_coupon=%s", last_coupon_date, next_coupon_date)
        # self.log.info("  [accint] days_in_period=%d, days_accrued=%d", days_in_period, days_accrued)
        # self.log.info(
        #     "  [accint] coupon_value=%s, accint_value=%s, accint_percent=%s",
        #     next_coupon_value, round(accint_value, 2), round(accint_percent, 4)
        # )

        return round(accint_value, 2), round(accint_percent, 4)

    async def _calc_bond(
        self,
        price: float,
        accint: float,
        days_to_redemption: int,
        sum_coupon_percent: float,
        commission: float = 0.3,
        tax: int = 13,
    ) -> float:
        """Калькуляция реальной годовой доходности от процентной цены"""

        year = 365

        # Расчет цены покупки (price уже в процентах от номинала)
        buy_price = price + accint
        commission_buy = buy_price * commission / 100
        final_price = buy_price + commission_buy

        # self.log.info("  [calc] buy_price=%s, commission=%s, final_price=%s", buy_price, commission_buy, final_price)

        # Расчет налога при продаже (100% — погашение по номиналу)
        sold_delta = 100 - final_price
        sold_tax = max(0, sold_delta * tax / 100)

        # self.log.info("  [calc] sold_delta=%s, sold_tax=%s", sold_delta, sold_tax)

        # Расчет купонного дохода и налога на купоны (сумма купона в процентах)
        coupon_tax = sum_coupon_percent * tax / 100

        # self.log.info("  [calc] coupon_tax=%s", coupon_tax)

        # Расчет общего дохода и процента годовой доходности
        income = (sold_delta + sum_coupon_percent) - (sold_tax + coupon_tax)
        profit = income / final_price * 100
        day_percent = profit / days_to_redemption
        year_percent = round(day_percent * year, 2)

        # self.log.info("  [calc] income=%s, profit=%s%%, day_percent=%s, year_percent=%s", income, profit, day_percent, year_percent)

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
        self.log.info("Время выполнения - %s", time_result)

from datetime import datetime, timedelta
import time
from urllib import parse

import requests


class Moex():
    '''Класс работы с API Московской биржи'''

    def build_url(self, method_url: str, params: dict) -> str:
        '''Конструктор url путей запросов к API moex'''

        base_url = 'https://iss.moex.com'
        url_parts = list(parse.urlparse(base_url))
        url_parts[2] = method_url
        url_parts[4] = parse.urlencode(params)
        result_url = parse.urlunparse(url_parts)

        return result_url


class MoexBond(Moex):
    '''Класс работы с облигациями Московской биржи'''
    def __init__(self, num_page: int = 100) -> None:
        self.num_page = num_page

    def get_list_bonds(self, page: int = 0, limit: int = 100) -> list:
        '''Получение списка облигаций одного запроса и первичное преоброзование
           Если облигация не торгуется возвращается пустой список
        '''

        method_url = '/iss/securities.json'
        start = page*limit
        params = {'iss.meta': 'off',
                  'securities.columns': 'secid, is_traded',
                  'engine': 'stock',
                  'market': 'bonds',
                  'start': start}
        list_bonds_url = self.build_url(method_url=method_url, params=params)
        raw_list_bonds = requests.get(list_bonds_url).json()

        secur = raw_list_bonds.get('securities')
        data = secur.get('data')
        if not data:
            return []
        columns = secur.get('columns')
        secid = columns.index('secid')
        is_traded = columns.index('is_traded')

        list_bonds = [i[secid] for i in data if i[is_traded] == 1]

        return list_bonds

    def generator_bonds(self) -> list:
        '''Генерирование последовательности списка облигаций со всей биржи'''

        start_time = datetime.now()

        for i in range(self.num_page):
            iter_time = datetime.now()
            delta = (iter_time - start_time).seconds
            delta = time.strftime("%M:%S", time.gmtime(delta))
            list_bonds = self.get_list_bonds(page=i)
            if list_bonds:
                print(f'{delta} --- Page {i}')
                yield list_bonds

    def get_detail_bond(self, secid: str) -> dict:
        '''Получение общей детальной информации по облигации'''

        method_url = f'/iss/securities/{secid}.json'
        params = {'iss.meta': 'off',
                  'description.columns': 'name, title, value',
                  'iss.only': 'description'}
        bond_url = self.build_url(method_url=method_url, params=params)
        bond = requests.get(bond_url).json()

        desc = bond.get('description')
        data = desc.get('data')
        columns = desc.get('columns')

        value = columns.index('value')
        name = columns.index('name')
        keys = ['shortname',
                'secid',
                'isin',
                'matdate',
                'initialfacevalue',
                'faceunit',
                'listlevel',
                'daystoredemption',
                'face_value',
                'isqualifiedinvestors',
                'couponfrequency',
                'coupondate',
                'couponpercent',
                'couponvalue',
                'group',
                'type']

        bond = {i[name].lower(): i[value] for i in data
                if i[name].lower() in keys}

        if (bond.get('isqualifiedinvestors') == '1' or
                not bond.get('couponfrequency')):
            return None

        bond = bond | self.get_effectiveyield(secid=secid)

        return bond

    def get_effectiveyield(self, secid: str) -> dict:
        '''Получение доходности, цены и НКД'''

        date_now = datetime.now()
        delta_date = date_now - timedelta(days=7)
        till_date = datetime.strftime(date_now, '%Y-%m-%d')
        from_date = datetime.strftime(delta_date, '%Y-%m-%d')

        method_url = f'/iss/history/engines/stock/markets/bonds/yields/{secid}.json'
        params = {'iss.meta': 'off',
                  'sort_order': 'desc',
                  'from': from_date,
                  'till': till_date,
                  'limit': 1}

        bond_url = self.build_url(method_url=method_url, params=params)
        bond_price = requests.get(bond_url).json()
        history_yields = bond_price.get('history_yields')
        try:
            data = history_yields.get('data')[0]
        except IndexError:
            return {}
        columns = history_yields.get('columns')
        price_params = ['price', 'accint', 'effectiveyield']
        bond = {i: data[columns.index(i.upper())] for i in price_params}

        return bond

    def calc_bond(self, secid: str,
                  commission: float = 0.3,
                  tax: int = 13) -> dict:
        '''Калькуляция реальной доходности'''

        year = 365
        bond = self.get_detail_bond(secid=secid)

        price = bond.get('price')
        accint = bond.get('accint')
        face_value = bond.get('facevalue')
        coupon_frequency = bond.get('couponfrequency')
        days_to_redemption = bond.get('daystoredemption')
        coupon_value = bond.get('couponvalue')

        buy_price = face_value*price/100 + accint
        commission_buy = buy_price*commission/100
        final_price = buy_price + commission_buy
        sold_delta = face_value - final_price
        sold_tax = sold_delta*tax/100
        if sold_delta < 0:
            sold_tax = 0

        coupon_day = year//coupon_frequency
        coupon_num = days_to_redemption//coupon_day + 1
        сoupon_sum = coupon_num*coupon_value
        coupon_tax = сoupon_sum*tax/100

        income = (sold_delta + сoupon_sum) - (sold_tax + coupon_tax)
        profit = income/final_price*100
        day_percent = profit/days_to_redemption
        year_percent = day_percent*year

        bond = bond | {'year_percent': year_percent}

        return bond

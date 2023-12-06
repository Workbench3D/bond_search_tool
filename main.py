from datetime import datetime, timedelta
from urllib import parse
import requests

from database import MoexORM


def build_url(method_url: str, params: dict) -> str:
    '''Конструктор url путей запросов к API moex'''

    base_url = 'https://iss.moex.com'
    url_parts = list(parse.urlparse(base_url))
    url_parts[2] = method_url
    url_parts[4] = parse.urlencode(params)
    result_url = parse.urlunparse(url_parts)

    return result_url


def get_list_bonds(start: int = 0) -> list:
    '''Получение списка облигаций и первичное преоброзование'''

    method_url = '/iss/securities.json'
    params = {'iss.meta': 'off',
              'securities.columns': 'isin, is_traded',
              'engine': 'stock',
              'market': 'bonds',
              'start': start}
    list_bonds_url = build_url(method_url=method_url, params=params)
    raw_list_bonds = requests.get(list_bonds_url).json()

    secur = raw_list_bonds.get('securities')
    data = secur.get('data')
    columns = secur.get('columns')
    isin = columns.index('isin')
    is_traded = columns.index('is_traded')

    list_bonds = [i[isin] for i in data if i[is_traded] == 1]

    return list_bonds


def get_detail_bond(isin: str) -> dict:
    '''Получение детальной информации по облигации'''

    method_url = f'/iss/securities/{isin}.json'
    params = {'iss.meta': 'off',
              'description.columns': 'name, title, value',
              'iss.only': 'description'}
    bond_url = build_url(method_url=method_url, params=params)
    bond = requests.get(bond_url).json()

    desc = bond.get('description')
    data = desc.get('data')
    columns = desc.get('columns')

    value = columns.index('value')
    name = columns.index('name')
    keys = ['shortname',
            'isin',
            'matdate',
            'initialfacevalue',
            'faceunit',
            'listlevel',
            'daystoredemption',
            'facevalue',
            'isqualifiedinvestors',
            'couponfrequency',
            'coupondate',
            'couponpercent',
            'couponvalue',
            'group',
            'type']

    bond = {i[name].lower(): i[value] for i in data if i[name].lower() in keys}

    if bond['isqualifiedinvestors'] == 1 or bond['faceunit'] != 'SUR':
        return None

    date_now = datetime.now()
    delta_date = date_now - timedelta(days=7)
    till_date = datetime.strftime(date_now, '%Y-%m-%d')
    from_date = datetime.strftime(delta_date, '%Y-%m-%d')

    method_url = f'/iss/history/engines/stock/markets/bonds/yields/{isin}.json'
    params = {'iss.meta': 'off',
              'sort_order': 'desc',
              'from': from_date,
              'till': till_date,
              'limit': 1}

    bond_url = build_url(method_url=method_url, params=params)
    bond_price = requests.get(bond_url).json()
    history_yields = bond_price.get('history_yields')
    data = history_yields.get('data')[0]
    columns = history_yields.get('columns')
    price_params = ['price', 'accint', 'effectiveyield']

    for i in price_params:
        index = columns.index(i.upper())
        bond[i] = data[index]

    bond = bond | calc_bond(bond=bond)

    return bond


def restructure_json():
    pass


def calc_bond(bond: dict) -> dict:
    '''Калькуляция реальной доходности'''
    try:
        face_value = int(bond.get('initialfacevalue'))
        price = bond.get('price') * face_value/100
        commission = price * 0.003
        accint = bond.get('accint')
        price_buy = price + commission + accint
        coupon_freq = int(bond.get('couponfrequency'))
        day_storedem = int(bond.get('daystoredemption'))
        coupon_value = float(bond.get('couponvalue'))

        tax_bond = (face_value - price_buy) * 0.13
        num_coupon = day_storedem // (365 // coupon_freq) + 1
        sum_coupon = num_coupon * coupon_value
        tax_coupon = sum_coupon * 0.13

        spent = price_buy + tax_bond + tax_coupon
        income = face_value + sum_coupon
        margin = income - spent
        profit = margin/price_buy*100
        day_percent = profit/day_storedem
        year_percent = day_percent*365
    except TypeError:
        return {'margin': None,
                'day_percent': None,
                'year_percent': None}

    return {'margin': margin,
            'day_percent': day_percent,
            'year_percent': year_percent}


if __name__ == '__main__':
    # t = get_detail_bond('RU000A0JQ5C5')
    MoexORM.create_tables()
    for i in range(80):
        start = i * 100
        list_bonds = get_list_bonds(start=start)
        for j in list_bonds:
            detail_bond = get_detail_bond(j)
            if detail_bond is None:
                continue
            MoexORM.insert_data(detail_bond)

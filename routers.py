from urllib import parse


class Moex():
    '''Класс работы с API Московской биржи'''
    def __init__(self) -> None:
        pass

    def build_url(method_url: str, params: dict) -> str:
        '''Конструктор url путей запросов к API moex'''

        base_url = 'https://iss.moex.com'
        url_parts = list(parse.urlparse(base_url))
        url_parts[2] = method_url
        url_parts[4] = parse.urlencode(params)
        result_url = parse.urlunparse(url_parts)

        return result_url

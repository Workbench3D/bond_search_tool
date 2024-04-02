from repositories.bond import MoexORM


def fastapi_service(
    fields: str | None = None,
    max_year_percent: int | None = None,
    min_year_percent: int | None = None,
    max_list_level: int | None = None,
    min_list_level: int | None = None,
    amortizations: bool | None = None,
    floater: bool | None = None,
    max_days_to_redemption: int | None = None,
    min_days_to_redemption: int | None = None,
    ofz_bonds: bool | None = None,
    limit: int | None = None,
):
    if fields is None:
        fields_list = [
            "shortname",
            "secid",
            "matdate",
            "face_unit",
            "list_level",
            "days_to_redemption",
            "face_value",
            "accint",
            "price",
            "sum_coupon",
            "year_percent",
        ]
    else:
        fields_list = fields.split(",")

    if max_year_percent is None:
        max_year_percent = 20
    if min_year_percent is None:
        min_year_percent = 5
    if max_list_level is None:
        max_list_level = 3
    if min_list_level is None:
        min_list_level = 1
    if amortizations is None:
        amortizations = False
    if floater is None:
        floater = False
    if max_days_to_redemption is None:
        max_days_to_redemption = 1500
    if min_days_to_redemption is None:
        min_days_to_redemption = 500
    if limit is None:
        limit = 50

    between_year_percent = (min_year_percent, max_year_percent)
    between_list_level = (min_list_level, max_list_level)
    between_days_to_redemption = (min_days_to_redemption, max_days_to_redemption)

    result = MoexORM.select_bonds(
        fields=fields_list,
        year_percent=between_year_percent,
        list_level=between_list_level,
        amortizations=amortizations,
        floater=floater,
        days_to_redemption=between_days_to_redemption,
        ofz_bonds=ofz_bonds,
        limit=limit,
    )

    return result

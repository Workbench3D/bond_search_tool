from repositories.bond import MoexORM


def fastapi_service(fields: str | None = None, limit: int | None = None):
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

    if limit is None:
        return MoexORM.select_bonds(fields=fields_list)

    return MoexORM.select_bonds(fields=fields_list, limit=limit)

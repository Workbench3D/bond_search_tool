from repositories.bond import MoexORM


def fastapi_service(fields: str | None = None, limit: int | None = None):

    if fields is None:
        fields = ['shortname',
                  'secid',
                  'matdate',
                  'face_unit',
                  'list_level',
                  'days_to_redemption',
                  'face_value',
                  'accint',
                  'price',
                  'sum_coupon',
                  'year_percent']
    else:
        fields = fields.split(',')

    if limit is None:
        return MoexORM.select_bonds(fields=fields)

    return MoexORM.select_bonds(fields=fields, limit=limit)

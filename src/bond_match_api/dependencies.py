from repository.bond import MoexORM


def fastapi_service(limit: int = 100,
                    fields: str | None = None) -> dict:

    if not fields:
        fields = 'shortname,secid,matdate,initialfacevalue,faceunit,listlevel,daystoredemption,facevalue,amortizations,floater,couponfrequency,coupondate,couponpercent,couponvalue,sumcoupon,highrisk,type,price,accint,effectiveyield,yearpercent'
    list_fields = fields.split(',')
    result = MoexORM.select_bonds(fields=list_fields, limit=limit)
    result = [list(i) for i in result]

    return {'fields': fields, 'data': result}

from fastapi import FastAPI
import uvicorn

# from api import router as api_router
from api.database import MoexORM
from api.service import BondList, Bond, ContextStrategy


app = FastAPI()

# app.include_router(api_router.router)


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/get_bonds')
async def get_bonds(limit: int | None = None,
                    fields: str | None = None) -> dict:
    if not fields:
        fields = 'shortname,secid,matdate,initialfacevalue,faceunit,listlevel,\
            daystoredemption,facevalue,amortizations,floater,couponfrequency,\
            coupondate,couponpercent,couponvalue,sumcoupon,highrisk,type,price,\
            accint,effectiveyield,yearpercent'
    fields = fields.split(',')
    result = MoexORM.select_bonds(fields=fields, limit=limit)
    result = [list(i) for i in result]

    return {'fields': fields, 'data': result}


@app.get('/update_info')
def get_info():
    bond = Bond()
    bond_list = BondList()
    client = ContextStrategy(bond_list)
    page = 0
    while True:
        try:
            client.set_strategy(bond_list)
            list_bonds = client.execute_strategy(page=page)
            page += 1
            client.set_strategy(bond)
            bonds = [detail for i in list_bonds
                     if (detail := client.execute_strategy(secid=i))]

            MoexORM.update_data(bonds=bonds)
        except StopIteration:
            break


if __name__ == '__main__':
    uvicorn.run('main:app',
                host='127.0.0.1',
                port=8000,
                reload=True,
                workers=3)

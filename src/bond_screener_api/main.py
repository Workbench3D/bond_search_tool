from typing import Annotated
from fastapi import FastAPI, Depends
import uvicorn

# from api import router as api_router
from dependencies import fastapi_service


app = FastAPI()

# app.include_router(api_router.router)


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/bonds')
async def get_bonds(
        fastapi_service: Annotated[dict, Depends(fastapi_service)]):
    return fastapi_service


if __name__ == '__main__':
    uvicorn.run('main:app',
                host='0.0.0.0',
                port=8000,
                reload=True,
                workers=3)

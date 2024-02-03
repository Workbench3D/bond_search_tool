import os
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

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
async def get_bonds(fastapi_service: Annotated[dict, Depends(fastapi_service)]) -> dict:
    return fastapi_service


if __name__ == '__main__':
    uvicorn.run('main:app',
                host='127.0.0.1',
                port=8000,
                reload=True,
                workers=3)

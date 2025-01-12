from typing import Annotated
from fastapi import FastAPI, Depends, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from schemas.bond import ColumnGroupModel
import uvicorn

# from api import router as api_router
from dependencies import fastapi_service


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# app.include_router(api_router.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bonds")
async def get_bonds(fastapi_service: Annotated[dict, Depends(fastapi_service)]):
    return fastapi_service


@app.get("/view_bonds", response_class=HTMLResponse)
async def get_view_bonds(
    request: Request,
    fastapi_service: Annotated[ColumnGroupModel, Depends(fastapi_service)],
    max_year_percent: int = Query(20),
    min_year_percent: int = Query(5),
    max_list_level: int = Query(3),
    min_list_level: int = Query(1),
    amortizations: bool = Query(False),
    floater: bool = Query(False),
    ofz_bonds: bool = Query(False),
    max_days_to_redemption: int = Query(1500),
    min_days_to_redemption: int = Query(500),
):
    columns = fastapi_service.columns
    data = fastapi_service.data
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "columns": columns,
            "data": data,
            "max_year_percent": max_year_percent,
            "min_year_percent": min_year_percent,
            "max_list_level": max_list_level,
            "min_list_level": min_list_level,
            "amortizations": amortizations,
            "floater": floater,
            "ofz_bonds": ofz_bonds,
            "max_days_to_redemption": max_days_to_redemption,
            "min_days_to_redemption": min_days_to_redemption,
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=3)

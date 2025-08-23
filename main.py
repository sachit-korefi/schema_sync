from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from config.database import get_db
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from DAO.base_dao import BaseDAO
from config import logger
from router.output_schema_router import schema_router
from router.user_router import user_router
from router.sync_router import sync_router


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all domains
    allow_credentials=False,  # No cookies or authentication
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)
app.include_router(schema_router)
app.include_router(user_router)
app.include_router(sync_router)

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/health_check")
def health_check():
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except OperationalError:
        return JSONResponse(content={"status": "db_error"}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
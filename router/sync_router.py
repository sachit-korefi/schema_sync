from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from config.logger import logger
from sqlalchemy.orm import Session
from config.database import get_db
from handler.sync_handler import SyncHandler
from typing import Dict, Any, List
import pandas as pd
import io

sync_router = APIRouter(prefix="/sync")

@sync_router.get("/", status_code=status.HTTP_200_OK)
async def sync_schema(
    sync_metadata: Dict[str, Any],
    files: List[UploadFile] = File(...),
    session: Session = Depends(get_db)):
    try:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "files processed successfully"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate Excel files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while generating Excel files"
        )

@sync_router.post("/get_excel_sheets", status_code=status.HTTP_200_OK)
async def get_excel_sheet_names(
    file: UploadFile = File(...),
):
    try:
        # Read the uploaded Excel file
        file_contents = await file.read()
        xls = pd.ExcelFile(io.BytesIO(file_contents))
        
        # Get the sheet names
        sheet_names = xls.sheet_names
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Excel sheets retrieved successfully",
                "sheet_names": sheet_names
            }
        )
    except Exception as e:
        logger.error(f"Failed to read Excel file sheets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading Excel file: {str(e)}"
        )
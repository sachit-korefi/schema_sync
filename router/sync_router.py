from fastapi import APIRouter, status, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from config.logger import logger
from sqlalchemy.orm import Session
from config.database import get_db
from handlers.sync_handlers.sync_handler import SyncHandler
from typing import Dict, Any, List
import pandas as pd
import zipfile
import json
import io

sync_router = APIRouter(prefix="/sync")

@sync_router.post("/", status_code=status.HTTP_200_OK)
async def sync_schema(
    sync_metadata: str = Form(None),
    files: List[UploadFile] = File(...),
    session: Session = Depends(get_db)):
    try:
        try:
            processed_metadata = json.loads(sync_metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sync_metadata format. Must be a valid JSON string."
            )

        sync_handler = SyncHandler(session=session)
        processed_files = await sync_handler.handle(sync_metadata=processed_metadata, files=files)
        
        
        if len(processed_files) == 1:
            # ✅ Single file case
            buffer = io.StringIO()
            filename = processed_files[0].get("filename")
            file = processed_files[0].get("file")
            file.to_csv(buffer, index=False)
            buffer.seek(0)

            return StreamingResponse(
                buffer,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # ✅ Multiple files → create ZIP in-memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, file_detail in enumerate(processed_files):
                    # Generate dynamic file name (e.g., from metadata or index)
                    filename = file_detail.get("filename", f"{idx}-default")
                    file = file.get("file")
                    
                    # Write DataFrame to in-memory string
                    buffer = io.StringIO()
                    file.to_csv(buffer, index=False)
                    zip_file.writestr(filename, buffer.getvalue())

            zip_buffer.seek(0)

            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=processed_files.zip"}
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
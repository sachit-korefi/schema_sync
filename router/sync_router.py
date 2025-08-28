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
    session: Session = Depends(get_db)
):
    try:
        # Parse metadata
        try:
            processed_metadata = json.loads(sync_metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sync_metadata format. Must be a valid JSON string."
            )

        # Process input files using handler
        sync_handler = SyncHandler(session=session)
        processed_files = await sync_handler.handle(sync_metadata=processed_metadata, files=files)

        if len(processed_files) == 1:
            # ✅ Single file case
            file_detail = processed_files[0]
            filename = file_detail.get("filename", "output.csv")
            file = file_detail.get("file")
            file_type = "csv" if filename.split(".")[-1] == "csv" else "excel"

            if file_type == "csv":
                # Write CSV to in-memory buffer
                buffer = io.StringIO()
                file.to_csv(buffer, index=False)
                buffer.seek(0)
                media_type = "text/csv"

                return StreamingResponse(
                    buffer,
                    media_type=media_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

            elif file_type == "excel":
                # file here is expected to be a dict {sheet_name: dataframe}
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    for sheet_name, df in file.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                excel_buffer.seek(0)
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                return StreamingResponse(
                    excel_buffer,
                    media_type=media_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

        else:
            # ✅ Multiple files → ZIP in-memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, file_detail in enumerate(processed_files):
                    filename = file_detail.get("filename", f"{idx+1}-default.csv")
                    file = file_detail.get("file")
                    file_type = "csv" if filename.split(".")[-1] == "csv" else "excel"

                    if file_type == "csv":
                        # Write CSV to memory
                        csv_buffer = io.StringIO()
                        file.to_csv(csv_buffer, index=False)
                        zip_file.writestr(filename, csv_buffer.getvalue())

                    elif file_type == "excel":
                        # Write Excel (with multiple sheets) to memory
                        excel_bytes = io.BytesIO()
                        with pd.ExcelWriter(excel_bytes, engine="xlsxwriter") as writer:
                            for sheet_name, df in file.items():
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                        zip_file.writestr(filename, excel_bytes.getvalue())

            zip_buffer.seek(0)

            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=processed_files.zip"}
            )

    except Exception as e:
        logger.error(f"Failed to generate files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error occurred while generating files : {e}"
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
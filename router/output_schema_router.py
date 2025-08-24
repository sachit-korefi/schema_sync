from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from config.logger import logger
from sqlalchemy.orm import Session
from fastapi import Depends
from config.database import get_db
from DAO.output_schema_dao import OutputSchemaDAO
from typing import Dict

schema_router = APIRouter(prefix="/schema")

@schema_router.get("/{schema_uuid}", status_code=status.HTTP_200_OK)
async def get_schema(schema_uuid: str, session: Session = Depends(get_db)):
    try:
        output_schema_dao = OutputSchemaDAO(session)
        output_schema = output_schema_dao.get_output_schema_by_schema_uuid(schema_uuid=schema_uuid)
        output_schema = output_schema.to_dict()
        
        if output_schema is None:
            logger.error(f"Schema with UUID '{schema_uuid}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with UUID '{schema_uuid}' not found"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Schema fetched sucessfully",
                "schema_uuid": schema_uuid,
                "user_uuid": output_schema["user_uuid"],
                "output_schema": output_schema["schema"]
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) so they're not caught by generic handler
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve schema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving schema"
        )

@schema_router.get("/get_all_schemas/{user_uuid}", status_code=status.HTTP_200_OK)
async def get_all_schemas(user_uuid: str, session: Session = Depends(get_db)):
    try:
        output_schema_dao = OutputSchemaDAO(session)
        output_schema = output_schema_dao.get_output_schemas_by_user_uuid(user_uuid=user_uuid)
        
        if output_schema == []:
            logger.error(f"Schemas with user UUID {user_uuid} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schemas with user UUID {user_uuid} not found"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Schemas fetched sucessfully",
                "user_uuid": output_schema[0]["user_uuid"],
                "output_schemas": output_schema,
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) so they're not caught by generic handler
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve schema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving schema"
        )

@schema_router.post("/{user_uuid}", status_code=status.HTTP_202_ACCEPTED)
async def create_schema(user_uuid: str, schema_json: Dict[str, str], session: Session = Depends(get_db)):
    try:
        output_schema_dao = OutputSchemaDAO(session)
        output_schema = output_schema_dao.create_output_schema(user_uuid=user_uuid, output_schema_json=schema_json)

        if output_schema is None:
            logger.error(f"Schema with UUID '{output_schema.schema_uuid}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with UUID '{output_schema.schema_uuid}' not found"
            )
        return JSONResponse(
            status_code=202,
            content={
                "message" : f"successfully created schema with schema uuid : {output_schema.schema_uuid}"
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) so they're not caught by generic handler
        raise
    except Exception as e:
        logger.error(f"Failed to create schema : {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "details": str(e)}
        )
    

@schema_router.put("/{schema_uuid}", status_code=status.HTTP_202_ACCEPTED)
async def update_schema(schema_uuid: str, schema_json: Dict[str, str], session: Session = Depends(get_db)):
    try:
        output_schema_dao = OutputSchemaDAO(session)
        is_updated = output_schema_dao.update_output_schema_by_schema_uuid(schema_uuid=schema_uuid, schema=schema_json)
        if is_updated == 0:
            logger.error(f"Schema with UUID {schema_uuid} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with UUID {schema_uuid} not found"
            )
        return JSONResponse(
            status_code=202,
            content={
                "message" : f"successfully updated schema with schema uuid : {schema_uuid}"
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) so they're not caught by generic handler
        raise
    except Exception as e:
        logger.error(f"Failed to update schema: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "details": str(e)}
        )
    

@schema_router.delete("/{schema_uuid}", status_code=status.HTTP_202_ACCEPTED)
async def delete_schema(schema_uuid: str, session: Session = Depends(get_db)):
    try:
        output_schema_dao = OutputSchemaDAO(session)
        is_deleted = output_schema_dao.delete_schema_by_schema_uuid(schema_uuid=schema_uuid)
        if is_deleted == 0:
            logger.error(f"Schema with UUID {schema_uuid} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with UUID {schema_uuid} not found"
            )
        return JSONResponse(
            status_code=202,
            content={
                "message" : f"successfully deleted schema with schema uuid : {schema_uuid}"
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) so they're not caught by generic handler
        raise
    except Exception as e:
        logger.error(f"Failed to delete schema : {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "details": str(e)}
        )

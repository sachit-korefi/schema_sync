from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from config.logger import logger
from sqlalchemy.orm import Session
from config.database import get_db
from DAO.user_dao import UserDAO
from typing import Dict, Any
import uuid

user_router = APIRouter(prefix="/user")

@user_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_users(session: Session = Depends(get_db)):
    try:
        user_dao = UserDAO(session)
        users = user_dao.get_all_users()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Users fetched successfully",
                "users": [user.to_dict() for user in users]
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving users"
        )

@user_router.get("/{user_uuid}", status_code=status.HTTP_200_OK)
async def get_user_details(user_uuid: str, session: Session = Depends(get_db)):
    try:
        user_dao = UserDAO(session)
        user_uuid_obj = uuid.UUID(user_uuid)
        user = user_dao.get_user_by_uuid(user_uuid_obj)
        
        if user is None:
            logger.error(f"User with UUID {user_uuid} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with UUID {user_uuid} not found"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User details fetched successfully",
                "user": user.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve user details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving user details"
        )

@user_router.put("/{user_uuid}", status_code=status.HTTP_202_ACCEPTED)
async def update_user_details(user_uuid: str, user_data: Dict[str, Any], session: Session = Depends(get_db)):
    try:
        user_dao = UserDAO(session)
        
        updated_rows = user_dao.update_user_by_uuid(user_uuid=user_uuid, update_data=user_data)
        
        if updated_rows == 0:
            logger.error(f"User with UUID {user_uuid} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with UUID {user_uuid} not found"
            )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": f"User with UUID {user_uuid} updated successfully"
            }
        )
    except Exception as e:
        logger.error(f"Failed to update user details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error", "details": str(e)}
        )

@user_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: Dict[str, str], session: Session = Depends(get_db)):
    try:
        # Validate required fields
        required_fields = ['user_email', 'user_firstname', 'user_lastname', 'user_password']
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Check if user with the same email already exists
        user_dao = UserDAO(session)
        existing_user = user_dao.get_user_by_email(user_data['user_email'])
        
        if existing_user:
            logger.error(f"User with email {user_data['user_email']} already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        # Create the user
        new_user = user_dao.create_user(user_data)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "User created successfully",
                "user": new_user.to_dict()
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions so they're not caught by the generic handler
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating user"
        )

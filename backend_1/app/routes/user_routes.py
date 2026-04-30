from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.database.connection import Database
from app.models import User, UserCreate
import logging

logger = logging.getLogger(__name__)

user_router = APIRouter()


@user_router.get("/", response_model=List[User])
async def get_users():
    """Get all users"""
    try:
        db = Database.get_database()
        users_cursor = db.users.find()
        users = []
        async for user in users_cursor:
            user["id"] = str(user["_id"])
            del user["_id"]
            users.append(User(**user))
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@user_router.post("/", response_model=User)
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        db = Database.get_database()
        user_dict = user.dict()
        result = await db.users.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)
        return User(**user_dict)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@user_router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    try:
        db = Database.get_database()
        user = await db.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user["id"] = str(user["_id"])
        del user["_id"]
        return User(**user)
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

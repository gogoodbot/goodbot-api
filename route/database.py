"""
database operations module
"""

import os
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

client: Client = create_client(
    os.environ.get("DATABASE_URL"),
    os.environ.get("DATABASE_API_KEY")
)

def user_exists(value: str):
    """
    check if user exists in database
    """
    try:
        response = client.table("users").select("*").eq("username", value.lower()).execute()
        return len(response.data) > 0 and response.data[0]["active"] == 1
    except Exception as e: # pylint: disable=broad-except
        print(f"Error checking if user exists: {e}")
        return False

def get_user_by_username(username: str):
    """
    get user from database by username
    """
    try:
        response = client.table("users").select("*").eq("username", username.lower()).execute()
        return response.data[0]
    except Exception as e: # pylint: disable=broad-except
        print(f"Error getting user by username: {e}")
        return None

def insert_user(username: str, hashed_password: str):
    """
    inserts new user into database
    """
    try:
        response = client.table("users")\
            .insert({"username": username.lower(), "password": hashed_password})\
            .execute()
        return response.data
    except Exception as e: # pylint: disable=broad-except
        print(f"Error inserting user into database: {e}")
        return None

def get_litigations():
    """
    get all litigations from database
    """
    try:
        response = client.table("Litigation").select("*").execute()
        return response.data
    except Exception as e: # pylint: disable=broad-except
        print(f"Error getting all litigations: {e}")
        return None

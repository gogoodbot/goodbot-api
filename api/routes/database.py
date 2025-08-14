"""
database operations module
"""

import os
from supabase import Client, create_client
from dotenv import load_dotenv

def get_database_client() -> Client:
    """
    create supabase client using environment variables
    """
    load_dotenv()

    client: Client = create_client(
        os.environ.get("DATABASE_URL"),
        os.environ.get("DATABASE_API_KEY")
    )
    return client

class DatabaseRepository:
    """
    repository class for database operations.
    This class encapsulates the database operations and provides methods to interact with the database.
    """
    def __init__(self):
        self.client = get_database_client()

    def user_exists(self, value: str):
        """
        check if user exists in database
        """
        try:
            response = self.client.table("users").select(
                "*").eq("username", value.lower()).execute()
            return len(response.data) > 0 and response.data[0]["active"] == 1
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error checking if user exists: {e}")
            return False


    def get_user_by_username(self, username: str):
        """
        get user from database by username
        """
        try:
            response = self.client.table("users").select(
                "*").eq("username", username.lower()).execute()
            return response.data[0]
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting user by username: {e}")
            return None


    def insert_user(self, username: str, hashed_password: str):
        """
        inserts new user into database
        """
        try:
            response = self.client.table("users")\
                .insert({"username": username.lower(), "password": hashed_password})\
                .execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error inserting user into database: {e}")
            return None


    def get_litigations(self):
        """
        get all litigations from database
        """
        try:
            response = self.client.table("Litigation").select("*").execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting all litigations: {e}")
            return None

    async def get_structural_subfactors(self):
        """
        get all structural subfactors from database
        """
        try:
            response = self.client.table("structural_sub_factors").select("*").execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting all structural subfactors: {e}")
            return None

    async def get_harm_and_risk_by_subfactor_id(self, subfactor_id: str):
        """
        get harm and risk by subfactor id from database
        :param subfactor_id: the id of the structural subfactor
        :return: list of harms and risks associated with the subfactor
        """
        try:
            response = self.client.table("harms_and_risks").select("*").eq("structural_sub_factor_id",subfactor_id).execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting harm and risk by id: {e}")
            return None

    async def get_nonprofits_by_harm_risk_id(self, harm_risk_id: str, page_number: int = 1, page_size: int = 4):
        """
        get nonprofit by given harm and risk id from nonprofits_and_harmsrisks reference/join table in database. Handles pagination.
        :param harm_risk_id: the id of the harm and risk
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of nonprofits associated with the harm and risk
        """
        try:
            response = self.client.table("nonprofits_and_harmrisks").select("*").eq("harm_risk_id", harm_risk_id).range(
                (page_number - 1) * page_size, page_number * page_size - 1
            ).execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting entity by nonprofit id: {e}")
            return None

    async def get_entity_by_nonprofit_id(self, nonprofit_id: str):
        """
        get entity by given nonprofit id from database
        :param nonprofit_id: the id of the nonprofit
        :return: entity data or None if not found
        """
        try:
            response = self.client.table("nonprofits").select("entity_id").eq("id", nonprofit_id).execute()
            if not response.data:
                print(f"Error getting entity by nonprofit id: {response}")
                return None
            entity_id = response.data[0]["entity_id"]
            response = self.client.table("entities").select("*").eq("id",entity_id).execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting entity by nonprofit id: {e}")
            return None

    def get_nonprofits(self, page_number: int = 1, page_size: int = 4):
        """
        get nonprofits from database. Handles pagination.
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of nonprofits
        """
        try:
            response = self.client.table("nonprofits").select("*").range(
                (page_number - 1) * page_size, page_number * page_size - 1
            ).execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting all nonprofits: {e}")
            return None

    async def get_experts_by_harm_risk_id(self, harm_risk_id: str, page_number: int = 1, page_size: int = 4):
        """
        get expert by given nonprofit id from database. Handles pagination.
        :param harm_risk_id: the id of the harm and risk
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of experts associated with the harm and risk
        """
        try:
            response = self.client.table("experts_and_harmrisks").select("*").eq("harm_risk_id", harm_risk_id).range(
                (page_number - 1) * page_size, page_number * page_size - 1
            ).execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting entity by nonprofit id: {e}")
            return None

    async def get_expert_by_id(self, expert_id: str, page_number: int = 1, page_size: int = 4):
        """
        get expert by given expert id from database. Handles pagination.
        :param expert_id: the id of the expert
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of experts associated with the harm and risk
        """
        try:
            response = self.client.table("experts").select("*").eq("id", expert_id).range(
                (page_number - 1) * page_size, page_number * page_size - 1
            ).execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting entity by nonprofit id: {e}")
            return None

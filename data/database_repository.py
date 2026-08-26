"""
database operations module
"""

from functools import lru_cache

from supabase import Client, create_client

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def get_database_client() -> Client:
    """
    create supabase client using environment variables
    Uses lru_cache to ensure we only create one client instance
    """
    logger.info("Creating Supabase client")
    client: Client = create_client(settings.database_url, settings.database_api_key)
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
            response = (
                self.client.table("users")
                .select("*")
                .eq("username", value.lower())
                .execute()
            )
            return len(response.data) > 0 and response.data[0]["active"] == 1
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error checking if user exists: {e}")
            return False

    def get_user_by_username(self, username: str):
        """
        get user from database by username
        """
        try:
            response = (
                self.client.table("users")
                .select("*")
                .eq("username", username.lower())
                .execute()
            )
            return response.data[0]
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting user by username: {e}")
            return None

    def insert_user(self, username: str, hashed_password: str):
        """
        inserts new user into database
        """
        try:
            response = (
                self.client.table("users")
                .insert({"username": username.lower(), "password": hashed_password})
                .execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error inserting user into database: {e}")
            return None

    def get_litigations(self):
        """
        get all litigations from database
        """
        try:
            response = self.client.table("Litigation").select("*").execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting all litigations: {e}")
            return None

    async def get_homepage_data(self):
        """
        get homepage data through join queries from database
        """
        try:
            response = self.client.rpc("get_homepage_data2").execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting homepage data: {e}")
            return None

    async def get_structural_subfactors(self):
        """
        get all structural subfactors from database
        """
        try:
            response = self.client.table("structural_sub_factors").select("*").execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting all structural subfactors: {e}")
            return None

    async def get_experts(self, page_number: int = 1, page_size: int = 10):
        """
        get experts from database. Handles pagination.
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of experts
        """
        try:
            # if page_size is -1, fetch all experts
            if page_size == -1:
                response = self.client.table("experts").select("*").execute()
                return response.data
            response = (
                self.client.table("experts")
                .select("*")
                .range((page_number - 1) * page_size, page_number * page_size - 1)
                .execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting all experts: {e}")
            return None

    async def get_expert_by_id(self, expert_id: str):
        """
        get expert by given expert id from database
        :param expert_id: the id of the expert
        :return: expert data or None if not found
        """
        try:
            response = (
                self.client.table("experts").select("*").eq("id", expert_id).execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting expert by id: {e}")
            return None

    async def update_expert_by_id(self, expert_id: str, update_data: dict):
        """
        update expert by given expert id in database
        :param expert_id: the id of the expert
        :param update_data: the data to update
        :return: updated expert data or None if not found
        """
        try:
            response = (
                self.client.table("experts")
                .update(update_data)
                .eq("id", expert_id)
                .execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error updating expert by id: {e}")
            return None

    async def get_nonprofits(self, page_number: int = 1, page_size: int = 4):
        """
        get nonprofits from database. Handles pagination.
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of nonprofits
        """
        try:
            response = (
                self.client.table("nonprofits")
                .select("*")
                .range((page_number - 1) * page_size, page_number * page_size - 1)
                .execute()
            )
            if not response.data:
                logger.error(f"Error getting all nonprofits: {response}")
                return None
            entities = []
            for nonprofit in response.data:
                entity = await self.get_entity_by_nonprofit_id(nonprofit["id"])
                if entity:
                    entities.append(entity[0])

            return entities
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting all nonprofits: {e}")
            return None

    async def get_entity_by_nonprofit_id(self, nonprofit_id: str):
        """
        get entity by given nonprofit id from database
        :param nonprofit_id: the id of the nonprofit
        :return: entity data or None if not found
        """
        try:
            response = (
                self.client.table("nonprofits")
                .select("entity_id")
                .eq("id", nonprofit_id)
                .execute()
            )
            if not response.data:
                logger.error(f"Error getting entity by nonprofit id: {response}")
                return None

            entity_id = response.data[0]["entity_id"]
            response = (
                self.client.table("entities").select("*").eq("id", entity_id).execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting entity by nonprofit id: {e}")
            return None

    async def get_entity_by_id(self, entity_id: str):
        """
        get entity by given entity id from database
        :param entity_id: the id of the entity
        :return: entity data or None if not found
        """
        try:
            response = (
                self.client.table("entities").select("*").eq("id", entity_id).execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting entity by id: {e}")
            return None

    async def get_entities(self, page_number: int = 1, page_size: int = 4):
        """
        get entities from database. Handles pagination.
        :param page_number: the page number to fetch
        :param page_size: the number of items per page
        :return: list of entities
        """
        try:
            # if page_size is -1, fetch all entities
            if page_size == -1:
                response = self.client.table("entities").select("*").execute()
                return response.data
            response = (
                self.client.table("entities")
                .select("*")
                .range((page_number - 1) * page_size, page_number * page_size - 1)
                .execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error getting all entities: {e}")
            return None

    async def update_entity_by_id(self, entity_id: str, update_data: dict):
        """
        update entity by given entity id in database
        :param entity_id: the id of the entity
        :param update_data: the data to update
        :return: updated entity data or None if not found
        """
        try:
            response = (
                self.client.table("entities")
                .update(update_data)
                .eq("id", entity_id)
                .execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error updating entity by id: {e}")
            return None

    async def search_by_keywords(self, keywords: str):
        """
        search entities, nonprofits and experts by given keywords in database
        :param keywords: the keywords to search
        :return: list of entities, nonprofits and experts matching the keywords
        """
        try:
            keywords = keywords.strip()

            result_experts = self.client.rpc(
                "search_experts_with_keyword", {"q": keywords}
            ).execute()

            result_entities = self.client.rpc(
                "search_entities_with_keyword", {"q": keywords}
            ).execute()

            # combine results into a json object
            response = {
                "nonprofits": result_entities.data,
                "experts": result_experts.data,
            }
            return response
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error searching by keywords: {e}")
            return None

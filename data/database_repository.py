"""
database operations module
"""

import re
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
    client: Client = create_client(
        settings.database_url, settings.database_api_key
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
            response = self.client.rpc("get_homepage_data").execute()
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting homepage data: {e}")
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
            print(f"Error getting all experts: {e}")
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
            print(f"Error getting expert by id: {e}")
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
            print(f"Error updating expert by id: {e}")
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
                print(f"Error getting all nonprofits: {response}")
                return None
            entities = []
            for nonprofit in response.data:
                entity = await self.get_entity_by_nonprofit_id(nonprofit["id"])
                if entity:
                    entities.append(entity[0])

            return entities
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting all nonprofits: {e}")
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
                print(f"Error getting entity by nonprofit id: {response}")
                return None

            entity_id = response.data[0]["entity_id"]
            response = (
                self.client.table("entities").select("*").eq("id", entity_id).execute()
            )
            return response.data
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error getting entity by nonprofit id: {e}")
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
            print(f"Error getting entity by id: {e}")
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
            print(f"Error getting all entities: {e}")
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
            print(f"Error updating entity by id: {e}")
            return None

    async def search_by_keywords(self, keywords: str):
        """
        search entities, nonprofits and experts by given keywords in database
        :param keywords: the keywords to search
        :return: list of entities, nonprofits and experts matching the keywords
        """
        try:
            # Sanitize input - remove special characters except alphanumeric, spaces, and hyphens
            keywords = re.sub(r'[^a-zA-Z0-9\s\-]', '', keywords)

            # Limit length to prevent DoS
            keywords = keywords[:500]

            # turn string keywords into an array or keywords
            keywords = keywords.replace(" ", ",")
            keywords_array = keywords.split(",")
            # Filter out empty strings
            keywords_array = [k.strip() for k in keywords_array if k.strip()]

            if not keywords_array:
                logger.warning("No valid keywords after sanitization")
                return {"nonprofits": [], "experts": []}

            # add single quotes (') around each keyword
            keywords_array = [f"'{keyword}'" for keyword in keywords_array]
            # join the keywords with | operator for full text search
            keywords = " | ".join(keywords_array)

            result_entities = (
                self.client.from_("entities")
                .select("id")
                .text_search("about", keywords)
                .execute()
            )

            result_experts = self.client.rpc(
                "search_experts_with_keyword", {"q": keywords}
            ).execute()

            # get nonprofits by entity ids
            result_nonprofits = []
            for entity in result_entities.data:
                nonprofits = (
                    self.client.table("nonprofits")
                    .select("*")
                    .eq("entity_id", entity["id"])
                    .execute()
                )
                if nonprofits.data:
                    result_nonprofits.extend(nonprofits.data)

            # filter result_entities to only include those with matching nonprofits
            result_entities.data = [
                entity
                for entity in result_entities.data
                if any(
                    nonprofit["entity_id"] == entity["id"]
                    for nonprofit in result_nonprofits
                )
            ]

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

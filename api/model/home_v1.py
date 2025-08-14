"""
home page data model
"""
from pydantic import BaseModel

class HomePageData(BaseModel):
    """
    home page data model
    """
    subfactors: list[dict]

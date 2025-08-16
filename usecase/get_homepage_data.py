"""
Use case for fetching homepage data including structural subfactors and their associated harms and risks.
Each harm and risk holds a list of nonprofits, experts, litigations, policies and resources.
"""
from model.home_v1 import HomePageData

class GetHomePageData:
    """Use case for fetching homepage data including structural subfactors and their associated items."""
    def __init__(self, repository):
        self.repository = repository

    async def execute(self):
        """
        Get composite homepage data which includes nonprofits, experts, litigations, policies and resources.
        """
        try:
            subfactors = await self.repository.get_homepage_data()

            # TODO: fetch experts, litigations, policies and resources for each harm and risk and add each of them as objects/keys to harms and risks object
            # harm_and_risk["litigations"] = self.repository.get_litigations_by_harm_and_risk_id(harm_and_risk["id"])
            # harm_and_risk["policies"] = self.repository.get_policies_by_harm_and_risk_id(harm_and_risk["id"])
            # harm_and_risk["resources"] = self.repository.get_resources_by_harm_and_risk_id(harm_and_risk["id"])

            return HomePageData(subfactors=subfactors)
        except Exception as e:
            print(f"Error fetching home page data: {e}")
            return {"message": "Error fetching home page data"}

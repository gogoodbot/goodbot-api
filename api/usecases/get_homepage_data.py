"""
Use case for fetching homepage data including structural subfactors and their associated harms and risks.
Each harm and risk holds a list of nonprofits, experts, litigations, policies and resources.
"""
from api.model.home_v1 import HomePageData

class GetHomePageData:
    """Use case for fetching homepage data including structural subfactors and their associated items."""
    def __init__(self, repository):
        self.repository = repository

    async def execute(self):
        """
        Get composite homepage data which includes nonprofits, experts, litigations, policies and resources.
        """
        try:
            subfactors = await self.repository.get_structural_subfactors()
            # iterate through each subfactor, fetch harms and risks by id and add them as a list of objects
            # to the subfactor object
            if not subfactors:
                return {
                    "message": "No structural subfactors found"
                }
            for subfactor in subfactors:
                harms_and_risks = await self.repository.get_harm_and_risk_by_subfactor_id(subfactor["id"])
                if harms_and_risks:
                    subfactor["harms_and_risks"] = harms_and_risks

                # iterate through each harm and risk, fetch nonprofits by id and add them as a list of objects
                # to the harm and risk object
                for harm_and_risk in harms_and_risks:
                    nonprofits_and_harm_risks = await self.repository.get_nonprofits_by_harm_risk_id(harm_and_risk["id"])
                    # add "nonprofits" key to the harm and risk object, then add a list of entities based on the nonprofit ids
                    if nonprofits_and_harm_risks:
                        entities = []
                        for nonprofit_and_harm_risk in nonprofits_and_harm_risks:
                            entity = await self.repository.get_entity_by_nonprofit_id(nonprofit_and_harm_risk["nonprofit_id"])
                            if entity:
                                entities += entity
                        harm_and_risk["nonprofits"] = entities

                    # TODO: fetch experts, litigations, policies and resources for each harm and risk and add each of them as objects/keys to harms and risks object
                    # harm_and_risk["experts"] = self.repository.get_experts_by_harm_and_risk_id(harm_and_risk["id"])
                    # harm_and_risk["litigations"] = self.repository.get_litigations_by_harm_and_risk_id(harm_and_risk["id"])
                    # harm_and_risk["policies"] = self.repository.get_policies_by_harm_and_risk_id(harm_and_risk["id"])
                    # harm_and_risk["resources"] = self.repository.get_resources_by_harm_and_risk_id(harm_and_risk["id"])

            return HomePageData(subfactors=subfactors)
        except Exception as e:
            print(f"Error fetching home page data: {e}")
            return {
                "message": "Error fetching home page data"
            }

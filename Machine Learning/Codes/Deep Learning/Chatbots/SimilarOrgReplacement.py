import requests
import json
import time
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrganizationProfile:
    """Data class to store organization properties"""
    name: str
    wikidata_id: str = ""
    industry: List[str] = None
    instance_of: List[str] = None
    headquarters: str = ""
    founded: str = ""
    employee_count: str = ""
    revenue: str = ""
    stock_exchange: List[str] = None
    subsidiaries: List[str] = None
    parent_organization: str = ""
    
    def __post_init__(self):
        if self.industry is None:
            self.industry = []
        if self.instance_of is None:
            self.instance_of = []
        if self.stock_exchange is None:
            self.stock_exchange = []
        if self.subsidiaries is None:
            self.subsidiaries = []

class KnowledgeGraphReplacer:
    """Main class for organization replacement using knowledge graphs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrganizationReplacer/1.0 (https://example.com/contact)'
        })
        
        # Cache to avoid repeated API calls
        self.cache = {}
        
        # Predefined mappings for common organization types
        self.org_type_mappings = {
            'Q4830453': 'business',  # business enterprise
            'Q6881511': 'enterprise',  # enterprise
            'Q783794': 'company',  # company
            'Q891723': 'public_company',  # public company
            'Q219577': 'technology_company',  # technology company
            'Q1616075': 'news_agency',  # news agency
            'Q11032': 'newspaper',  # newspaper
            'Q1002697': 'news_media',  # news media
            'Q22687': 'bank',  # bank
            'Q856234': 'investment_bank',  # investment bank
            'Q18127': 'airline',  # airline
            'Q786820': 'automotive_company',  # automotive company
            'Q507619': 'pharmaceutical_company',  # pharmaceutical company
        }
    
    def search_entity_wikidata(self, entity_name: str) -> Optional[str]:
        """Search for entity in Wikidata and return entity ID"""
        if entity_name in self.cache:
            return self.cache[entity_name].get('wikidata_id')
        
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": entity_name,
            "language": "en",
            "format": "json",
            "type": "item",
            "limit": 5
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("search"):
                # Look for the most relevant match (usually first one for organizations)
                for result in data["search"]:
                    if result.get("description", "").lower().find("organi") != -1 or \
                       result.get("description", "").lower().find("company") != -1 or \
                       result.get("description", "").lower().find("corporation") != -1:
                        return result["id"]
                
                # If no organization-specific match, return the first result
                return data["search"][0]["id"]
        
        except Exception as e:
            logger.error(f"Error searching Wikidata for {entity_name}: {e}")
        
        return None
    
    def get_entity_properties(self, entity_id: str) -> Dict:
        """Get detailed properties of an entity from Wikidata"""
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "format": "json",
            "props": "claims|labels",
            "languages": "en"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "entities" in data and entity_id in data["entities"]:
                return data["entities"][entity_id]
        
        except Exception as e:
            logger.error(f"Error getting properties for {entity_id}: {e}")
        
        return {}
    
    def extract_property_values(self, claims: Dict, property_id: str) -> List[str]:
        """Extract values for a specific property from Wikidata claims"""
        values = []
        if property_id in claims:
            for claim in claims[property_id]:
                try:
                    if claim["mainsnak"]["snaktype"] == "value":
                        datavalue = claim["mainsnak"]["datavalue"]
                        if datavalue["type"] == "wikibase-entityid":
                            values.append(datavalue["value"]["id"])
                        elif datavalue["type"] == "string":
                            values.append(datavalue["value"])
                        elif datavalue["type"] == "time":
                            values.append(datavalue["value"]["time"])
                        elif datavalue["type"] == "quantity":
                            values.append(str(datavalue["value"]["amount"]))
                except (KeyError, TypeError):
                    continue
        return values
    
    def build_organization_profile(self, entity_name: str) -> Optional[OrganizationProfile]:
        """Build comprehensive organization profile from knowledge graph"""
        # Check cache first
        if entity_name in self.cache:
            return self.cache[entity_name]
        
        # Search for entity
        entity_id = self.search_entity_wikidata(entity_name)
        if not entity_id:
            logger.warning(f"Could not find Wikidata entity for {entity_name}")
            return None
        
        # Get entity properties
        entity_data = self.get_entity_properties(entity_id)
        if not entity_data:
            return None
        
        claims = entity_data.get("claims", {})
        
        # Extract relevant properties
        profile = OrganizationProfile(
            name=entity_name,
            wikidata_id=entity_id,
            instance_of=self.extract_property_values(claims, "P31"),  # instance of
            industry=self.extract_property_values(claims, "P452"),  # industry
            headquarters=self.extract_property_values(claims, "P159"),  # headquarters
            founded=self.extract_property_values(claims, "P571"),  # inception
            employee_count=self.extract_property_values(claims, "P1128"),  # employees
            revenue=self.extract_property_values(claims, "P2139"),  # revenue
            stock_exchange=self.extract_property_values(claims, "P414"),  # stock exchange
            subsidiaries=self.extract_property_values(claims, "P355"),  # subsidiaries
            parent_organization=self.extract_property_values(claims, "P749")  # parent organization
        )
        
        # Cache the result
        self.cache[entity_name] = profile
        return profile
    
    def calculate_similarity_score(self, org1: OrganizationProfile, org2: OrganizationProfile) -> float:
        """Calculate similarity score between two organizations"""
        score = 0.0
        total_weight = 0.0
        
        # Industry similarity (high weight)
        if org1.industry and org2.industry:
            industry_overlap = len(set(org1.industry) & set(org2.industry))
            industry_union = len(set(org1.industry) | set(org2.industry))
            if industry_union > 0:
                score += (industry_overlap / industry_union) * 0.4
            total_weight += 0.4
        
        # Instance type similarity (high weight)
        if org1.instance_of and org2.instance_of:
            instance_overlap = len(set(org1.instance_of) & set(org2.instance_of))
            instance_union = len(set(org1.instance_of) | set(org2.instance_of))
            if instance_union > 0:
                score += (instance_overlap / instance_union) * 0.3
            total_weight += 0.3
        
        # Stock exchange similarity (medium weight)
        if org1.stock_exchange and org2.stock_exchange:
            exchange_overlap = len(set(org1.stock_exchange) & set(org2.stock_exchange))
            exchange_union = len(set(org1.stock_exchange) | set(org2.stock_exchange))
            if exchange_union > 0:
                score += (exchange_overlap / exchange_union) * 0.2
            total_weight += 0.2
        
        # Parent organization similarity (medium weight)
        if org1.parent_organization and org2.parent_organization:
            if set(org1.parent_organization) & set(org2.parent_organization):
                score += 0.1
            total_weight += 0.1
        
        # Normalize score
        return score / total_weight if total_weight > 0 else 0.0
    
    def get_organization_type(self, profile: OrganizationProfile) -> str:
        """Determine the primary type of organization"""
        if not profile.instance_of:
            return "unknown"
        
        # Check for specific organization types
        for instance_id in profile.instance_of:
            if instance_id in self.org_type_mappings:
                return self.org_type_mappings[instance_id]
        
        return "business"  # default
    
    def find_similar_organizations(self, target_org: str, candidates: List[str], 
                                 min_similarity: float = 0.3, max_results: int = 5) -> List[Tuple[str, float]]:
        """Find similar organizations from a list of candidates"""
        target_profile = self.build_organization_profile(target_org)
        if not target_profile:
            logger.error(f"Could not build profile for target organization: {target_org}")
            return []
        
        similar_orgs = []
        
        for candidate in candidates:
            if candidate.lower() == target_org.lower():
                continue  # Skip the same organization
            
            candidate_profile = self.build_organization_profile(candidate)
            if not candidate_profile:
                continue
            
            similarity = self.calculate_similarity_score(target_profile, candidate_profile)
            
            if similarity >= min_similarity:
                similar_orgs.append((candidate, similarity))
            
            # Add small delay to respect API rate limits
            time.sleep(0.1)
        
        # Sort by similarity score (descending)
        similar_orgs.sort(key=lambda x: x[1], reverse=True)
        return similar_orgs[:max_results]
    
    def get_replacement_suggestion(self, target_org: str, candidates: List[str] = None) -> Optional[str]:
        """Get a single replacement suggestion for an organization"""
        if candidates is None:
            # Use a default list of well-known organizations
            candidates = [
                "Microsoft", "Google", "Apple", "Amazon", "Meta", "Tesla", "IBM", "Oracle",
                "Reuters", "CNN", "BBC", "Associated Press", "Bloomberg", "Wall Street Journal",
                "JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Bank of America",
                "Ford", "General Motors", "Toyota", "BMW", "Volkswagen",
                "Delta Air Lines", "American Airlines", "United Airlines", "Southwest Airlines",
                "Pfizer", "Johnson & Johnson", "Merck", "Novartis", "Roche"
            ]
        
        similar_orgs = self.find_similar_organizations(target_org, candidates, min_similarity=0.2, max_results=1)
        
        if similar_orgs:
            return similar_orgs[0][0]  # Return the most similar organization
        
        return None
    
    def replace_organization_in_text(self, text: str, target_org: str, replacement_org: str = None) -> str:
        """Replace organization name in text with a similar organization"""
        if replacement_org is None:
            replacement_org = self.get_replacement_suggestion(target_org)
        
        if replacement_org:
            # Simple replacement (could be enhanced with NER for better accuracy)
            return text.replace(target_org, replacement_org)
        
        return text
    
    def batch_replace_organizations(self, text: str, organizations: List[str]) -> Tuple[str, Dict[str, str]]:
        """Replace multiple organizations in text and return mapping"""
        replacements = {}
        modified_text = text
        
        for org in organizations:
            replacement = self.get_replacement_suggestion(org)
            if replacement:
                replacements[org] = replacement
                modified_text = modified_text.replace(org, replacement)
        
        return modified_text, replacements

# Example usage and testing
def main():
    """Example usage of the KnowledgeGraphReplacer"""
    replacer = KnowledgeGraphReplacer()
    
    # Example 1: Find similar organizations
    print("=== Finding Similar Organizations ===")
    target = "Microsoft"
    candidates = ["Google", "Apple", "Amazon", "Tesla", "Reuters", "Goldman Sachs", "Ford"]
    
    similar = replacer.find_similar_organizations(target, candidates)
    print(f"Organizations similar to {target}:")
    for org, score in similar:
        print(f"  {org}: {score:.3f}")
    
    # Example 2: Get single replacement suggestion
    print(f"\n=== Single Replacement Suggestion ===")
    replacement = replacer.get_replacement_suggestion("Reuters")
    print(f"Replacement for Reuters: {replacement}")
    
    # Example 3: Replace in text
    print(f"\n=== Text Replacement ===")
    sample_text = "Microsoft announced a new partnership with OpenAI. The Reuters news agency reported on this development."
    
    # Replace organizations
    new_text, mapping = replacer.batch_replace_organizations(
        sample_text, 
        ["Microsoft", "Reuters"]
    )
    
    print(f"Original: {sample_text}")
    print(f"Modified: {new_text}")
    print(f"Mappings: {mapping}")

if __name__ == "__main__":
    main()
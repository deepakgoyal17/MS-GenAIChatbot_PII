import spacy
import random
import json
import re
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Dict, List, Tuple, Optional, Set, Union
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
import hashlib

@dataclass
class OrganizationInfo:
    """Data class to store organization information"""
    name: str
    category: str
    industry: str
    confidence: float
    source: str  # 'database', 'web', 'generated'

class HybridOrganizationReplacer:
    """
    Hybrid replacer: Lightning fast for known orgs, dynamic discovery for unknown ones
    """
    
    def __init__(self, model_name: str = "en_core_web_sm", 
                 enable_web_fallback: bool = True,
                 web_timeout: float = 2.0,
                 max_web_requests: int = 5):
        """Initialize with hybrid approach settings"""
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Model '{model_name}' not found. Please install it using:")
            print(f"python -m spacy download {model_name}")
            raise
        
        self.enable_web_fallback = enable_web_fallback
        self.web_timeout = web_timeout
        self.max_web_requests = max_web_requests
        
        # Multi-level caching system
        self.fast_cache = {}  # Known organizations
        self.dynamic_cache = {}  # Dynamically discovered
        self.failed_lookups = set()  # Skip repeated failures
        self.web_request_count = 0
        
        # Initialize fast database
        self._initialize_core_database()
        
        # Dynamic pattern learning
        self.learned_patterns = {}
        self.industry_signals = {}
        
        # Thread pool for async web lookups
        self.web_executor = ThreadPoolExecutor(max_workers=3)
        self.pending_lookups = {}  # Track ongoing web lookups
        
        print(f"🚀 Initialized with {sum(len(orgs) for orgs in self.core_db.values())} known organizations")
        print(f"🌐 Web fallback: {'Enabled' if enable_web_fallback else 'Disabled'}")
    
    def _initialize_core_database(self):
        """Initialize core database with most common organizations"""
        
        self.core_db = {
            'technology': [
                # Top 50 most commonly mentioned tech companies
                'Apple', 'Microsoft', 'Google', 'Amazon', 'Meta', 'Tesla', 'Netflix',
                'Adobe', 'Salesforce', 'Oracle', 'IBM', 'Intel', 'NVIDIA', 'Cisco',
                'ServiceNow', 'Zoom', 'Slack', 'Shopify', 'PayPal', 'Uber', 'Airbnb',
                'Spotify', 'Twitter', 'LinkedIn', 'TikTok', 'Samsung', 'Sony', 'OpenAI',
                'Anthropic', 'DeepMind', 'Figma', 'Notion', 'Discord', 'Reddit', 'Dropbox'
            ],
            'finance': [
                'JPMorgan Chase', 'Bank of America', 'Wells Fargo', 'Citigroup',
                'Goldman Sachs', 'Morgan Stanley', 'BlackRock', 'Visa', 'Mastercard',
                'American Express', 'Capital One', 'Charles Schwab', 'Robinhood',
                'Stripe', 'Square', 'Coinbase', 'Fidelity', 'Vanguard'
            ],
            'healthcare': [
                'Johnson & Johnson', 'Pfizer', 'Moderna', 'UnitedHealth', 'CVS Health',
                'Merck', 'AbbVie', 'Bristol Myers Squibb', 'Eli Lilly', 'Amgen',
                'Walgreens', 'Kaiser Permanente', 'Anthem', 'Humana', 'Cigna'
            ],
            'retail': [
                'Walmart', 'Amazon', 'Target', 'Costco', 'Home Depot', 'Starbucks',
                'McDonald\'s', 'Nike', 'Coca-Cola', 'PepsiCo', 'Procter & Gamble'
            ],
            'automotive': [
                'Tesla', 'Ford', 'General Motors', 'Toyota', 'BMW', 'Mercedes-Benz',
                'Volkswagen', 'Honda', 'Nissan', 'Hyundai', 'Rivian', 'Lucid Motors'
            ],
            'media': [
                'Disney', 'Netflix', 'Warner Bros', 'Comcast', 'CNN', 'BBC',
                'New York Times', 'Washington Post', 'Reuters', 'Bloomberg'
            ],
            'education': [
                'Harvard University', 'Stanford University', 'MIT', 'Yale University',
                'Princeton University', 'Columbia University', 'UC Berkeley', 'UCLA'
            ],
            'aerospace': [
                'Boeing', 'Airbus', 'SpaceX', 'Blue Origin', 'Lockheed Martin',
                'American Airlines', 'Delta Air Lines', 'United Airlines'
            ]
        }
        
        # Create reverse lookup
        self.org_to_industry = {}
        for industry, orgs in self.core_db.items():
            for org in orgs:
                self.org_to_industry[org.lower()] = industry
        
        # Industry detection patterns
        self.industry_patterns = {
            'technology': [
                'tech', 'software', 'ai', 'digital', 'cyber', 'cloud', 'data', 'app',
                'platform', 'systems', 'solutions', 'computing', 'internet', 'mobile'
            ],
            'finance': [
                'bank', 'financial', 'capital', 'fund', 'investment', 'credit', 'loan',
                'insurance', 'trading', 'securities', 'fintech', 'payments', 'crypto'
            ],
            'healthcare': [
                'health', 'medical', 'pharma', 'bio', 'clinic', 'hospital', 'care',
                'therapeutics', 'diagnostics', 'wellness', 'medicine', 'treatment'
            ],
            'retail': [
                'retail', 'store', 'shop', 'market', 'brand', 'consumer', 'fashion',
                'commerce', 'merchandise', 'sales', 'shopping', 'marketplace'
            ],
            'automotive': [
                'auto', 'car', 'vehicle', 'motor', 'automotive', 'transport', 'mobility',
                'electric', 'ev', 'manufacturing', 'assembly'
            ],
            'media': [
                'media', 'news', 'broadcasting', 'entertainment', 'publishing', 'content',
                'streaming', 'production', 'studios', 'network', 'channel'
            ],
            'education': [
                'university', 'college', 'school', 'education', 'academic', 'institute',
                'learning', 'research', 'campus', 'faculty', 'student'
            ],
            'energy': [
                'energy', 'oil', 'gas', 'power', 'electric', 'renewable', 'solar',
                'wind', 'nuclear', 'utilities', 'grid', 'fuel'
            ],
            'aerospace': [
                'aerospace', 'aviation', 'airline', 'aircraft', 'flight', 'space',
                'defense', 'military', 'rocket', 'satellite'
            ]
        }
    
    @lru_cache(maxsize=2000)
    def fast_categorize_organization(self, org_name: str) -> Tuple[str, float]:
        """Fast categorization with confidence score"""
        org_lower = org_name.lower()
        
        # Method 1: Direct lookup (highest confidence)
        if org_lower in self.org_to_industry:
            return self.org_to_industry[org_lower], 1.0
        
        # Method 2: Learned patterns from previous discoveries
        if org_lower in self.learned_patterns:
            return self.learned_patterns[org_lower], 0.8
        
        # Method 3: Fuzzy matching with known organizations
        best_match_industry = None
        best_similarity = 0
        
        for known_org, industry in self.org_to_industry.items():
            similarity = SequenceMatcher(None, org_lower, known_org).ratio()
            if similarity > best_similarity and similarity > 0.7:
                best_similarity = similarity
                best_match_industry = industry
        
        if best_match_industry:
            return best_match_industry, best_similarity
        
        # Method 4: Pattern matching
        pattern_scores = {}
        for industry, patterns in self.industry_patterns.items():
            score = sum(1 for pattern in patterns if pattern in org_lower)
            if score > 0:
                pattern_scores[industry] = score
        
        if pattern_scores:
            best_industry = max(pattern_scores, key=pattern_scores.get)
            confidence = min(0.6, pattern_scores[best_industry] * 0.2)
            return best_industry, confidence
        
        # Method 5: Special case detection
        if any(term in org_lower for term in ['university', 'college', 'school']):
            return 'education', 0.7
        elif any(term in org_lower for term in ['bank', 'financial']):
            return 'finance', 0.7
        elif any(term in org_lower for term in ['hospital', 'medical', 'health']):
            return 'healthcare', 0.7
        
        return 'technology', 0.3  # Default with low confidence
    
    def discover_organization_web(self, org_name: str) -> Optional[OrganizationInfo]:
        """Discover organization info from web with smart timeout"""
        
        if not self.enable_web_fallback:
            return None
            
        if org_name in self.failed_lookups:
            return None
            
        if self.web_request_count >= self.max_web_requests:
            return None
        
        try:
            self.web_request_count += 1
            
            # Try Wikipedia first (fast and reliable)
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{org_name.replace(' ', '_')}"
            response = requests.get(wiki_url, timeout=self.web_timeout)
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get('extract', '').lower()
                
                if extract and len(extract) > 50:  # Meaningful content
                    industry, confidence = self.categorize_from_description(extract)
                    
                    org_info = OrganizationInfo(
                        name=org_name,
                        category=industry,
                        industry=industry,
                        confidence=confidence,
                        source='web'
                    )
                    
                    # Learn from this discovery
                    self.learned_patterns[org_name.lower()] = industry
                    self.dynamic_cache[org_name] = org_info
                    
                    print(f"🌐 Discovered: {org_name} → {industry} (confidence: {confidence:.2f})")
                    return org_info
            
            # If Wikipedia fails, try a simple industry classifier
            industry, confidence = self.fast_categorize_organization(org_name)
            if confidence > 0.5:
                org_info = OrganizationInfo(
                    name=org_name,
                    category=industry,
                    industry=industry,
                    confidence=confidence,
                    source='inferred'
                )
                self.dynamic_cache[org_name] = org_info
                return org_info
                
        except Exception as e:
            print(f"⚠️  Web lookup failed for {org_name}: {str(e)[:50]}...")
            self.failed_lookups.add(org_name)
        
        return None
    
    def categorize_from_description(self, description: str) -> Tuple[str, float]:
        """Categorize organization from description text"""
        desc_lower = description.lower()
        
        # Count industry-specific terms
        industry_scores = {}
        for industry, patterns in self.industry_patterns.items():
            score = sum(1 for pattern in patterns if pattern in desc_lower)
            if score > 0:
                industry_scores[industry] = score
        
        if not industry_scores:
            return 'technology', 0.3
        
        best_industry = max(industry_scores, key=industry_scores.get)
        max_score = industry_scores[best_industry]
        
        # Calculate confidence based on score and description length
        confidence = min(0.9, max_score * 0.15 + len(description) * 0.001)
        
        return best_industry, confidence
    
    def get_similar_organizations_hybrid(self, org_name: str, count: int = 5) -> List[str]:
        """Hybrid approach: Fast for known, dynamic for unknown"""
        
        # Step 1: Fast categorization
        industry, confidence = self.fast_categorize_organization(org_name)
        
        # Step 2: Get candidates from core database
        core_candidates = self.core_db.get(industry, [])
        similar_orgs = [
            org for org in core_candidates 
            if org.lower() != org_name.lower()
        ]
        
        # Step 3: If we have enough high-confidence matches, return them
        if len(similar_orgs) >= count and confidence > 0.7:
            random.shuffle(similar_orgs)
            return similar_orgs[:count]
        
        # Step 4: For unknown organizations, try web discovery (async if possible)
        if confidence < 0.7 and self.enable_web_fallback:
            # Try to get better info about this organization
            org_info = self.discover_organization_web(org_name)
            
            if org_info and org_info.confidence > confidence:
                industry = org_info.industry
                confidence = org_info.confidence
                
                # Get fresh candidates with new industry
                core_candidates = self.core_db.get(industry, [])
                similar_orgs = [
                    org for org in core_candidates 
                    if org.lower() != org_name.lower()
                ]
        
        # Step 5: Add candidates from related industries if needed
        if len(similar_orgs) < count:
            related_industries = self._get_related_industries(industry)
            for related_industry in related_industries:
                if len(similar_orgs) >= count * 2:  # Get extras for variety
                    break
                additional = [
                    org for org in self.core_db.get(related_industry, [])
                    if org not in similar_orgs and org.lower() != org_name.lower()
                ]
                similar_orgs.extend(additional)
        
        # Step 6: Generate synthetic organizations if still not enough
        while len(similar_orgs) < count:
            synthetic = self.generate_contextual_organization(org_name, industry)
            if synthetic not in similar_orgs:
                similar_orgs.append(synthetic)
        
        random.shuffle(similar_orgs)
        return similar_orgs[:count]
    
    def _get_related_industries(self, industry: str) -> List[str]:
        """Get related industries for better variety"""
        relationships = {
            'technology': ['finance', 'media', 'healthcare'],
            'finance': ['technology', 'healthcare', 'retail'],
            'healthcare': ['technology', 'finance'],
            'retail': ['technology', 'media'],
            'media': ['technology', 'entertainment'],
            'automotive': ['technology', 'energy'],
            'energy': ['technology', 'automotive'],
            'aerospace': ['technology', 'automotive'],
            'education': ['technology', 'healthcare']
        }
        return relationships.get(industry, ['technology'])
    
    def generate_contextual_organization(self, org_name: str, industry: str) -> str:
        """Generate realistic organization names based on context"""
        
        # Extract base name
        base_name = re.sub(r'\s+(Inc|Corp|Ltd|Company|Co|Group|LLC|LLP|Solutions|Systems|Technologies)\.?$', 
                          '', org_name, flags=re.IGNORECASE).strip()
        
        # Context-aware generation
        if len(base_name.split()) > 1:
            # Multi-word names: use variations
            words = base_name.split()
            variations = [
                f"{words[0]} {industry.title()}",
                f"Global {words[-1]}",
                f"{words[-1]} Enterprises",
                f"Premier {' '.join(words[:2])}"
            ]
        else:
            # Single word: add industry context
            variations = [
                f"{base_name} Technologies",
                f"Advanced {base_name}",
                f"{base_name} Group",
                f"Global {base_name}",
                f"{base_name} Solutions"
            ]
        
        # Industry-specific suffixes
        industry_suffixes = {
            'technology': ['Tech', 'Systems', 'Digital', 'Solutions'],
            'finance': ['Financial', 'Capital', 'Investment', 'Securities'],
            'healthcare': ['Health', 'Medical', 'Care', 'Bio'],
            'retail': ['Retail', 'Commerce', 'Brands', 'Market'],
            'education': ['Institute', 'Academy', 'University', 'College']
        }
        
        suffixes = industry_suffixes.get(industry, ['Corp', 'Group', 'Enterprises'])
        variations.extend([f"{base_name} {suffix}" for suffix in suffixes[:2]])
        
        return random.choice(variations)
    
    def extract_organizations(self, text: str) -> List[Tuple[str, int, int]]:
        """Extract organizations using NER"""
        doc = self.nlp(text)
        return [(ent.text, ent.start_char, ent.end_char) for ent in doc.ents if ent.label_ == "ORG"]
    
    def replace_organizations_hybrid(self, text: str, replacement_strategy: str = 'smart',
                                   custom_mapping: Dict[str, str] = None) -> Tuple[str, Dict[str, str], Dict[str, str]]:
        """
        Hybrid replacement with detailed reporting
        
        Returns:
            Tuple of (modified_text, replacements, metadata)
        """
        
        organizations = self.extract_organizations(text)
        if not organizations:
            return text, {}, {}
        
        replacements_made = {}
        metadata = {}
        organizations.sort(key=lambda x: x[1], reverse=True)
        
        modified_text = text
        
        for org_name, start_pos, end_pos in organizations:
            replacement = None
            source = 'unknown'
            
            # Custom mapping first
            if custom_mapping and org_name in custom_mapping:
                replacement = custom_mapping[org_name]
                source = 'custom'
            else:
                # Hybrid approach
                industry, confidence = self.fast_categorize_organization(org_name)
                
                if confidence > 0.7:
                    # High confidence - use fast method
                    similar_orgs = self.core_db.get(industry, [])
                    if similar_orgs:
                        candidates = [org for org in similar_orgs if org.lower() != org_name.lower()]
                        if candidates:
                            replacement = random.choice(candidates)
                            source = 'database'
                
                if not replacement:
                    # Unknown or low confidence - use dynamic discovery
                    similar_orgs = self.get_similar_organizations_hybrid(org_name, count=5)
                    if similar_orgs:
                        replacement = random.choice(similar_orgs)
                        source = 'dynamic'
                
                # Final fallback
                if not replacement:
                    replacement = self.generate_contextual_organization(org_name, industry)
                    source = 'generated'
            
            # Apply replacement
            if replacement:
                modified_text = modified_text[:start_pos] + replacement + modified_text[end_pos:]
                replacements_made[org_name] = replacement
                metadata[org_name] = {
                    'source': source,
                    'industry': industry if 'industry' in locals() else 'unknown',
                    'confidence': confidence if 'confidence' in locals() else 0.0
                }
        
        return modified_text, replacements_made, metadata
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        return {
            'core_database': {
                'organizations': sum(len(orgs) for orgs in self.core_db.values()),
                'industries': len(self.core_db)
            },
            'dynamic_discoveries': {
                'learned_patterns': len(self.learned_patterns),
                'cached_discoveries': len(self.dynamic_cache),
                'failed_lookups': len(self.failed_lookups)
            },
            'web_usage': {
                'requests_made': self.web_request_count,
                'max_requests': self.max_web_requests,
                'enabled': self.enable_web_fallback
            },
            'cache_performance': {
                'categorization_hits': self.fast_categorize_organization.cache_info().hits,
                'categorization_misses': self.fast_categorize_organization.cache_info().misses
            }
        }

def main():
    """Demonstrate hybrid approach handling known and unknown organizations"""
    
    print("🚀 Initializing Hybrid Organization Replacer...")
    replacer = HybridOrganizationReplacer(
        enable_web_fallback=True,
        web_timeout=2.0,
        max_web_requests=10
    )
    
    # Test with mix of known and unknown organizations
    test_texts = [
        # Known organizations (will be fast)
        """Apple and Microsoft are partnering with Google on new AI initiatives.
           Tesla collaborates with Ford while Netflix competes with Disney.""",
        
        # Mix of known and unknown
        """TechFlow Solutions received funding from Andreessen Horowitz.
           The startup CloudNinja is competing with established players like AWS.
           Regional bank FirstTrust Financial serves the midwest market.""",
        
        # Mostly unknown organizations  
        """BioInnovate Labs announced a breakthrough in gene therapy.
           The consulting firm StrategyMax advisors helped MegaCorp restructure.
           Local retailer ShopSmart expanded to three new states."""
    ]
    
    print("\n" + "="*80 + "\n")
    
    for i, text in enumerate(test_texts):
        print(f"📝 Test Text {i+1}:")
        print(f"Original: {text}")
        
        start_time = time.time()
        modified_text, replacements, metadata = replacer.replace_organizations_hybrid(text)
        processing_time = time.time() - start_time
        
        print(f"\n⚡ Processed in {processing_time:.3f} seconds")
        print(f"Modified: {modified_text}")
        
        print(f"\n🔄 Replacements & Sources:")
        for original, replacement in replacements.items():
            meta = metadata[original]
            print(f"  {original} → {replacement}")
            print(f"    Source: {meta['source']}, Industry: {meta['industry']}, Confidence: {meta['confidence']:.2f}")
        
        print("\n" + "-"*60 + "\n")
    
    # Show system statistics
    print("📊 System Performance Statistics:")
    stats = replacer.get_system_stats()
    for category, data in stats.items():
        print(f"\n{category.upper()}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    
    print(f"\n✅ Hybrid approach successfully handled both known and unknown organizations!")
    print(f"🎯 Fast path for known orgs, dynamic discovery for unknown ones")

if __name__ == "__main__":
    main()
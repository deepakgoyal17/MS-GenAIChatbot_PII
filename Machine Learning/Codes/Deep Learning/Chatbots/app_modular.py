#!/usr/bin/env python3
"""
Modular PII Protection Chatbot with Feature Flags
Enhanced version with configurable features
"""

import os
import warnings
import time
import re
import math
from typing import Dict, Any, Optional, Tuple

# Set offline mode for transformers to prevent network calls when models are cached
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# Core imports
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import os

# Custom modules
from config import PIIProtectionConfig, create_config_sidebar, create_preset_selector
from excel_exporter import PIIAnalysisExporter
from base_logger import BaseLogger
import logging

# Initialize logger
logger = BaseLogger(log_name='chatbot_app_modular', log_level=logging.INFO, log_dir='logs').get_logger()
logger.info("Modular chatbot application started")

# Conditional imports based on features
def load_conditional_imports(config: PIIProtectionConfig):
    """Load imports only when features are enabled"""
    imports = {}
    
    try:
        if config.enable_fake_names or config.enable_xxxx_masking:
            import spacy
            from faker import Faker
            imports['spacy'] = spacy
            imports['faker'] = Faker()
            logger.info("Loaded spaCy and Faker for NER processing")
    except ImportError as e:
        logger.error(f"Failed to load NER dependencies: {e}")
        st.error("⚠️ spaCy or Faker not available. NER features will be disabled.")
    
    try:
        if config.enable_fake_names and config.enable_smart_org_replacement:
            from SimilarOrgReplacement_BetterPerformance import HybridOrganizationReplacer
            imports['org_replacer'] = HybridOrganizationReplacer
            logger.info("Loaded smart organization replacer")
    except ImportError as e:
        logger.error(f"Failed to load organization replacer: {e}")
    
    try:
        if config.enable_fake_names and config.enable_capitalization:
            from capitalizeNameAndOrg import NameOrganizationCapitalizer
            imports['capitalizer'] = NameOrganizationCapitalizer
            logger.info("Loaded name capitalizer")
    except ImportError as e:
        logger.error(f"Failed to load capitalizer: {e}")
    
    try:
        if config.enable_llm_pii_removal:
            from local_llm_pii_removal import remove_pii_with_llm
            imports['llm_pii_remover'] = remove_pii_with_llm
            logger.info("Loaded LLM PII remover")
    except ImportError as e:
        logger.error(f"Failed to load LLM PII remover: {e}")
    
    try:
        if config.enable_semantic_similarity:
            from sentence_transformers import SentenceTransformer, util
            imports['sentence_transformers'] = (SentenceTransformer, util)
            logger.info("Loaded SentenceTransformers")
    except ImportError as e:
        logger.error(f"Failed to load SentenceTransformers: {e}")
    
    try:
        if config.enable_deepeval:
            from deepeval.models import DeepEvalBaseLLM
            from deepeval.metrics import AnswerRelevancyMetric
            from deepeval.test_case import LLMTestCase
            imports['deepeval'] = (DeepEvalBaseLLM, AnswerRelevancyMetric, LLMTestCase)
            logger.info("Loaded DeepEval")
    except ImportError as e:
        logger.error(f"Failed to load DeepEval: {e}")
    
    return imports

# Load environment variables
load_dotenv()

# API key validation
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ **API Key Missing**: GEMINI_API_KEY not found in environment variables.")
    st.info("Please add your Gemini API key to the .env file: GEMINI_API_KEY=your_key_here")
    st.info("Get your key from: https://aistudio.google.com/app/apikey")
    st.stop()

# Configure Gemini AI
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    logger.info("Gemini AI configured successfully")
except Exception as e:
    st.error(f"❌ Failed to configure Gemini AI: {str(e)}")
    st.info("Please check your GEMINI_API_KEY in the .env file")
    st.stop()

# Streamlit page configuration
st.set_page_config(
    page_title="PII Protection Chatbot",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔒 PII Protection Chatbot - Modular Research Platform")
st.markdown("Compare different PII protection methods with configurable features")

# Create configuration sidebar
create_preset_selector()
config = create_config_sidebar()

# Load conditional imports based on configuration
imports = load_conditional_imports(config)

# Initialize models based on configuration
@st.cache_resource(show_spinner=False)
def get_sentence_transformer_model():
    """Load SentenceTransformer model if semantic similarity is enabled"""
    if not config.enable_semantic_similarity:
        return None
    
    if 'sentence_transformers' not in imports:
        return None
    
    SentenceTransformer, util = imports['sentence_transformers']
    
    models_to_try = ['all-MiniLM-L6-v2', 'paraphrase-MiniLM-L6-v2', 'all-mpnet-base-v2']
    
    for model_name in models_to_try:
        try:
            logger.info(f"Attempting to load SentenceTransformer model: {model_name}")
            os.environ.pop('TRANSFORMERS_OFFLINE', None)
            os.environ.pop('HF_HUB_OFFLINE', None)
            
            model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded model: {model_name}")
            
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            return model
        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            continue
    
    st.warning("⚠️ SentenceTransformer models unavailable. Semantic similarity disabled.")
    return None

@st.cache_resource(show_spinner=False)
def get_spacy_model():
    """Load spaCy model if NER features are enabled"""
    if not (config.enable_fake_names or config.enable_xxxx_masking):
        return None
    
    if 'spacy' not in imports:
        return None
    
    try:
        spacy = imports['spacy']
        return spacy.load("en_core_web_sm")
    except OSError:
        st.error("⚠️ spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
        return None

# Initialize models
st_model = get_sentence_transformer_model()
nlp = get_spacy_model()

# Initialize Excel exporter if enabled
excel_exporter = None
if config.enable_excel_export:
    excel_exporter = PIIAnalysisExporter(output_dir="analysis_results", logger=logger)

# Initialize CustomLLM for DeepEval if enabled
custom_llm = None
if config.enable_deepeval and 'deepeval' in imports:
    DeepEvalBaseLLM, AnswerRelevancyMetric, LLMTestCase = imports['deepeval']
    
    class CustomLLM(DeepEvalBaseLLM):
        def __init__(self):
            self.model = genai.GenerativeModel("models/gemini-2.5-flash")
            self.model_name = "gemini-2.5-flash"

        def load_model(self):
            """Required abstract method for DeepEvalBaseLLM"""
            return self.model

        def generate(self, prompt: str) -> str:
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip() if response and response.text else "No response"
            except Exception as e:
                logger.error(f"Error generating content: {e}")
                return f"Error: {str(e)}"

        async def a_generate(self, prompt: str) -> str:
            return self.generate(prompt)

        def get_model_name(self):
            return self.model_name
    
    custom_llm = CustomLLM()

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# PII Processing Functions
def smart_org_replacement(text: str) -> str:
    """Smart organization replacement with fallback"""
    if not config.enable_smart_org_replacement or 'org_replacer' not in imports:
        # Fallback to simple faker
        if 'faker' in imports:
            return imports['faker'].company()
        return "ORGANIZATION"
    
    try:
        replacer = imports['org_replacer'](
            enable_web_fallback=True,
            web_timeout=2.0,
            max_web_requests=10
        )
        return replacer.replace_organizations_hybrid(text)[0]
    except Exception as e:
        logger.error(f"Smart org replacement failed: {e}")
        return imports['faker'].company() if 'faker' in imports else "ORGANIZATION"

def smart_capitalize(text: str) -> str:
    """Smart capitalization with fallback"""
    if not config.enable_capitalization or 'capitalizer' not in imports:
        return text
    
    try:
        capitalizer = imports['capitalizer'](method='spacy')
        capitalized_text, _ = capitalizer.capitalize_text(text)
        return capitalized_text
    except Exception as e:
        logger.error(f"Smart capitalization failed: {e}")
        return text

def fake_ner_replace(text: str, nlp_model=None, config_param=None, imports_param=None) -> Tuple[str, Dict[str, str]]:
    """Replace PII with fake data"""
    # Use passed config or global config
    current_config = config_param if config_param is not None else config
    # Use passed imports or global imports
    current_imports = imports_param if imports_param is not None else imports

    if not current_config.enable_fake_names or nlp_model is None or 'faker' not in current_imports:
        return text, {}
    
    try:
        # Apply smart capitalization if enabled
        if current_config.enable_capitalization:
            text = smart_capitalize(text)

        doc = nlp_model(text)
        faker = current_imports['faker']
        ner_map = {}
        real_to_fake = {}
        fake_text = text
        
        # Process spaCy entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]:
                if ent.text not in real_to_fake:
                    if ent.label_ == "PERSON":
                        real_to_fake[ent.text] = faker.name()
                    elif ent.label_ == "ORG":
                        real_to_fake[ent.text] = smart_org_replacement(ent.text)
                    elif ent.label_ == "GPE":
                        real_to_fake[ent.text] = faker.city()
                    elif ent.label_ == "DATE":
                        real_to_fake[ent.text] = faker.date()
                    elif ent.label_ == "EMAIL":
                        real_to_fake[ent.text] = faker.email()
                    elif ent.label_ == "PHONE":
                        real_to_fake[ent.text] = faker.phone_number()
                
                fake_value = real_to_fake[ent.text]
                ner_map[fake_value] = ent.text
                fake_text = fake_text.replace(ent.text, fake_value)
        
        # Regex fallback if enabled
        if current_config.enable_regex_fallback:
            # Email pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, fake_text)
            for email in emails:
                if email not in [v for v in ner_map.values()]:
                    fake_email = faker.email()
                    ner_map[fake_email] = email
                    fake_text = fake_text.replace(email, fake_email)

            # Phone pattern
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, fake_text)
            for phone in phones:
                if phone not in [v for v in ner_map.values()]:
                    fake_phone = faker.phone_number()
                    ner_map[fake_phone] = phone
                    fake_text = fake_text.replace(phone, fake_phone)
        
        return fake_text, ner_map
        
    except Exception as e:
        logger.error(f"Fake NER replacement failed: {e}")
        return text, {}

def mask_ner_with_xxxx(text: str, nlp_model=None, config_param=None, imports_param=None) -> Tuple[str, Dict[str, str]]:
    """Mask PII with XXXX"""
    # Use passed config or global config
    current_config = config_param if config_param is not None else config
    # Use passed imports or global imports
    current_imports = imports_param if imports_param is not None else imports

    if not current_config.enable_xxxx_masking or nlp_model is None:
        return text, {}
    
    try:
        # Apply smart capitalization if enabled
        if current_config.enable_capitalization:
            text = smart_capitalize(text)

        doc = nlp_model(text)
        mask_map = {}
        masked_text = text
        
        # Process spaCy entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]:
                mask_map[f"XXXX_{len(mask_map)}"] = ent.text
                masked_text = masked_text.replace(ent.text, "XXXX")
        
        # Regex fallback if enabled
        if current_config.enable_regex_fallback:
            # Email pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, masked_text)
            for email in emails:
                if email not in mask_map.values():
                    mask_map[f"XXXX_{len(mask_map)}"] = email
                    masked_text = masked_text.replace(email, "XXXX")
            
            # Phone pattern
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, masked_text)
            for phone in phones:
                if phone not in mask_map.values():
                    mask_map[f"XXXX_{len(mask_map)}"] = phone
                    masked_text = masked_text.replace(phone, "XXXX")
        
        return masked_text, mask_map
        
    except Exception as e:
        logger.error(f"XXXX masking failed: {e}")
        return text, {}

def restore_fake_ner(text: str, ner_map: Dict[str, str]) -> str:
    """Restore real names from fake names"""
    for fake_value, real_value in ner_map.items():
        text = text.replace(fake_value, real_value)
    return text

def calculate_semantic_similarity(responses: Dict[str, str]) -> Dict[str, float]:
    """Calculate semantic similarity between responses"""
    if not config.enable_semantic_similarity or st_model is None:
        return {}
    
    try:
        SentenceTransformer, util = imports['sentence_transformers']
        
        similarities = {}
        embeddings = {}
        
        # Generate embeddings
        for method, response in responses.items():
            embeddings[method] = st_model.encode(response, convert_to_tensor=True)
        
        # Calculate pairwise similarities
        methods = list(responses.keys())
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                sim_key = f"similarity_{method1}_{method2}"
                similarities[sim_key] = float(util.cos_sim(embeddings[method1], embeddings[method2]))
        
        return similarities
        
    except Exception as e:
        logger.error(f"Semantic similarity calculation failed: {e}")
        return {}

def calculate_deepeval_scores(prompts_responses: Dict[str, Tuple[str, str]]) -> Dict[str, float]:
    """Calculate DeepEval relevancy scores"""
    if not config.enable_deepeval or custom_llm is None or 'deepeval' not in imports:
        return {}
    
    try:
        DeepEvalBaseLLM, AnswerRelevancyMetric, LLMTestCase = imports['deepeval']
        scores = {}
        
        for method, (prompt, response) in prompts_responses.items():
            try:
                test_case = LLMTestCase(input=prompt, actual_output=response)
                relevancy_metric = AnswerRelevancyMetric(model=custom_llm)
                relevancy_metric.measure(test_case)
                scores[f"relevancy_{method}"] = relevancy_metric.score
                logger.info(f"DeepEval score for {method}: {relevancy_metric.score}")
            except Exception as e:
                logger.error(f"DeepEval failed for {method}: {e}")
                scores[f"relevancy_{method}"] = 0.0
        
        return scores
        
    except Exception as e:
        logger.error(f"DeepEval calculation failed: {e}")
        return {}

def calculate_pii_leakage(original_prompt: str, responses: Dict[str, str], nlp_model=None) -> Dict[str, int]:
    """Calculate PII leakage scores"""
    if not config.enable_pii_leakage_detection or nlp_model is None:
        return {}

    try:
        doc = nlp_model(original_prompt)
        real_entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]

        leakage_scores = {}
        for method, response in responses.items():
            leakage_count = sum(1 for entity in real_entities if entity in response)
            leakage_scores[f"pii_leakage_{method}"] = leakage_count
            leakage_scores[f"f1_{method}"] = 1 if leakage_count == 0 else 0

        return leakage_scores

    except Exception as e:
        logger.error(f"PII leakage calculation failed: {e}")
        return {}

def calculate_pii_leakage_rate(original_prompt: str, responses: Dict[str, str], nlp_model=None) -> Dict[str, float]:
    """Calculate PII leakage rate as percentage"""
    if not config.enable_pii_leakage_detection or nlp_model is None:
        return {}

    try:
        doc = nlp_model(original_prompt)
        real_entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]
        total_entities = len(real_entities)

        if total_entities == 0:
            return {f"pii_leakage_rate_{method}": 0.0 for method in responses.keys()}

        leakage_rates = {}
        for method, response in responses.items():
            leakage_count = sum(1 for entity in real_entities if entity in response)
            leakage_rates[f"pii_leakage_rate_{method}"] = (leakage_count / total_entities) * 100.0

        return leakage_rates

    except Exception as e:
        logger.error(f"PII leakage rate calculation failed: {e}")
        return {}

def calculate_detailed_pii_leakage_rate(original_prompt: str, responses: Dict[str, str], nlp_model=None) -> Dict[str, Any]:
    """Calculate detailed PII leakage rate metrics including per-entity-type breakdown"""
    if not config.enable_pii_leakage_detection or nlp_model is None:
        return {}

    try:
        doc = nlp_model(original_prompt)
        real_entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]

        # Group entities by type
        entity_types = {}
        for entity_text, entity_label in real_entities:
            if entity_label not in entity_types:
                entity_types[entity_label] = []
            entity_types[entity_label].append(entity_text)

        total_entities = len(real_entities)
        detailed_metrics = {}

        if total_entities == 0:
            # Return zero metrics for all methods
            for method in responses.keys():
                detailed_metrics.update({
                    f"pii_leakage_rate_{method}": 0.0,
                    f"pii_leakage_count_{method}": 0,
                    f"pii_leakage_severity_{method}": "LOW",
                    f"entities_detected_{method}": 0
                })
                for entity_type in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]:
                    detailed_metrics.update({
                        f"{entity_type.lower()}_leakage_rate_{method}": 0.0,
                        f"{entity_type.lower()}_leakage_count_{method}": 0
                    })
            return detailed_metrics

        for method, response in responses.items():
            # Overall leakage metrics
            leakage_count = sum(1 for entity_text, _ in real_entities if entity_text in response)
            leakage_rate = (leakage_count / total_entities) * 100.0

            # Determine severity level
            if leakage_rate == 0:
                severity = "NONE"
            elif leakage_rate <= 25:
                severity = "LOW"
            elif leakage_rate <= 50:
                severity = "MEDIUM"
            elif leakage_rate <= 75:
                severity = "HIGH"
            else:
                severity = "CRITICAL"

            detailed_metrics.update({
                f"pii_leakage_rate_{method}": leakage_rate,
                f"pii_leakage_count_{method}": leakage_count,
                f"pii_leakage_severity_{method}": severity,
                f"entities_detected_{method}": total_entities
            })

            # Per-entity-type leakage
            for entity_type, entities in entity_types.items():
                type_count = len(entities)
                type_leaked = sum(1 for entity_text in entities if entity_text in response)
                type_leakage_rate = (type_leaked / type_count) * 100.0 if type_count > 0 else 0.0

                detailed_metrics.update({
                    f"{entity_type.lower()}_leakage_rate_{method}": type_leakage_rate,
                    f"{entity_type.lower()}_leakage_count_{method}": type_leaked
                })

            # Log PLR events for monitoring
            if leakage_count > 0:
                logger.warning(f"PLR ALERT - Method '{method}': {leakage_count}/{total_entities} entities leaked ({leakage_rate:.1f}%) - Severity: {severity}")
                for entity_text, entity_label in real_entities:
                    if entity_text in response:
                        logger.warning(f"PLR DETECTED - {entity_label}: '{entity_text}' found in {method} response")

        return detailed_metrics

    except Exception as e:
        logger.error(f"Detailed PII leakage rate calculation failed: {e}")
        return {}

def calculate_pii_leakage_trends(session_data: list) -> Dict[str, Any]:
    """Calculate PII leakage trends across multiple queries"""
    if not session_data:
        return {}

    try:
        trends = {}
        methods = set()

        # Collect all methods from session data
        for record in session_data:
            for key in record.keys():
                if key.startswith("pii_leakage_rate_"):
                    method = key.replace("pii_leakage_rate_", "")
                    methods.add(method)

        methods = sorted(list(methods))

        for method in methods:
            leakage_rates = []
            for record in session_data:
                rate_key = f"pii_leakage_rate_{method}"
                if rate_key in record and record[rate_key] is not None:
                    leakage_rates.append(record[rate_key])

            if leakage_rates:
                trends.update({
                    f"avg_plr_{method}": sum(leakage_rates) / len(leakage_rates),
                    f"max_plr_{method}": max(leakage_rates),
                    f"min_plr_{method}": min(leakage_rates),
                    f"std_plr_{method}": (sum((x - sum(leakage_rates)/len(leakage_rates))**2 for x in leakage_rates) / len(leakage_rates))**0.5 if len(leakage_rates) > 1 else 0,
                    f"queries_analyzed_{method}": len(leakage_rates)
                })

                # PLR trend analysis
                if len(leakage_rates) >= 3:
                    recent_avg = sum(leakage_rates[-3:]) / 3
                    overall_avg = sum(leakage_rates) / len(leakage_rates)
                    trend_direction = "STABLE"
                    if recent_avg > overall_avg * 1.1:
                        trend_direction = "INCREASING"
                    elif recent_avg < overall_avg * 0.9:
                        trend_direction = "DECREASING"

                    trends[f"plr_trend_{method}"] = trend_direction

        return trends

    except Exception as e:
        logger.error(f"PII leakage trends calculation failed: {e}")
        return {}

def calculate_reidentification_risk(original_prompt: str, responses: Dict[str, str], nlp_model=None) -> Dict[str, Any]:
    """Calculate comprehensive re-identification risk metrics"""
    if not config.enable_pii_leakage_detection or nlp_model is None:
        return {}

    try:
        doc = nlp_model(original_prompt)
        real_entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]

        if len(real_entities) < 2:
            return {f"reidentification_risk_{method}": 0.0 for method in responses.keys()}

        reidentification_metrics = {}

        # Group entities by type for more detailed analysis
        entity_types = {}
        for entity_text, entity_label in real_entities:
            if entity_label not in entity_types:
                entity_types[entity_label] = []
            entity_types[entity_label].append(entity_text)

        for method, response in responses.items():
            response_doc = nlp_model(response)
            response_entities = [(ent.text, ent.label_) for ent in response_doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]

            # Calculate pairwise entity combination preservation
            preserved_combinations = 0
            total_combinations = len(real_entities) * (len(real_entities) - 1) // 2

            # Track which specific combinations are preserved
            preserved_pairs = []
            if total_combinations > 0:
                for i, (ent1, label1) in enumerate(real_entities):
                    for j, (ent2, label2) in enumerate(real_entities[i+1:], i+1):
                        ent1_present = any(ent1 in resp_ent[0] for resp_ent in response_entities)
                        ent2_present = any(ent2 in resp_ent[0] for resp_ent in response_entities)
                        if ent1_present and ent2_present:
                            preserved_combinations += 1
                            preserved_pairs.append(f"{ent1}({label1})-{ent2}({label2})")

            combination_risk = (preserved_combinations / total_combinations) * 100.0 if total_combinations > 0 else 0.0

            # Calculate entity frequency risk (how many entities from original appear)
            entity_frequency_risk = (len(set(ent[0] for ent in real_entities) & set(ent[0] for ent in response_entities)) / len(real_entities)) * 100.0

            # Calculate uniqueness risk (how unique the entity combination is)
            # Simplified: based on number of preserved pairs relative to total possible pairs
            uniqueness_factor = min(1.0, preserved_combinations / max(1, total_combinations))
            uniqueness_risk = uniqueness_factor * 100.0

            # Overall re-identification risk (weighted combination)
            overall_risk = (combination_risk * 0.5 + entity_frequency_risk * 0.3 + uniqueness_risk * 0.2)

            # Determine risk level
            if overall_risk == 0:
                risk_level = "NONE"
            elif overall_risk <= 25:
                risk_level = "LOW"
            elif overall_risk <= 50:
                risk_level = "MEDIUM"
            elif overall_risk <= 75:
                risk_level = "HIGH"
            else:
                risk_level = "CRITICAL"

            reidentification_metrics.update({
                f"reidentification_risk_{method}": overall_risk,
                f"reidentification_risk_level_{method}": risk_level,
                f"combination_preservation_{method}": combination_risk,
                f"entity_frequency_risk_{method}": entity_frequency_risk,
                f"uniqueness_risk_{method}": uniqueness_risk,
                f"preserved_combinations_{method}": preserved_combinations,
                f"total_combinations_{method}": total_combinations
            })

            # Log high-risk re-identification events
            if overall_risk > 50:
                logger.warning(f"RE-ID ALERT - Method '{method}': High re-identification risk ({overall_risk:.1f}%) - Level: {risk_level}")
                if preserved_pairs:
                    logger.warning(f"RE-ID DETECTED - Preserved combinations: {', '.join(preserved_pairs[:3])}")

        return reidentification_metrics

    except Exception as e:
        logger.error(f"Re-identification risk calculation failed: {e}")
        return {}

def calculate_bleu_score(responses: Dict[str, str], reference_text: str = None) -> Dict[str, float]:
    """Calculate BLEU score comparing responses against reference text"""
    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        bleu_scores = {}

        # Use the first response as reference if not provided
        if reference_text is None and len(responses) > 1:
            # Use 'real' response as reference if available, otherwise first response
            reference_text = responses.get('real', next(iter(responses.values())))

        if not reference_text:
            return {f"bleu_score_{method}": 0.0 for method in responses.keys()}

        # Tokenize reference
        reference_tokens = reference_text.lower().split()

        smoothing = SmoothingFunction().method1

        for method, response in responses.items():
            if method == 'real' and reference_text == responses.get('real'):
                # Skip BLEU for reference text itself
                bleu_scores[f"bleu_score_{method}"] = 1.0
                continue

            candidate_tokens = response.lower().split()

            if len(candidate_tokens) == 0:
                bleu_scores[f"bleu_score_{method}"] = 0.0
                continue

            try:
                # Calculate BLEU score with smoothing
                bleu = sentence_bleu([reference_tokens], candidate_tokens, smoothing_function=smoothing)
                bleu_scores[f"bleu_score_{method}"] = bleu
            except Exception as e:
                logger.warning(f"BLEU calculation failed for {method}: {e}")
                bleu_scores[f"bleu_score_{method}"] = 0.0

        return bleu_scores

    except ImportError:
        logger.warning("NLTK not available for BLEU score calculation")
        return {f"bleu_score_{method}": 0.0 for method in responses.keys()}
    except Exception as e:
        logger.error(f"BLEU score calculation failed: {e}")
        return {f"bleu_score_{method}": 0.0 for method in responses.keys()}

def calculate_rouge_scores(responses: Dict[str, str], reference_text: str = None) -> Dict[str, Any]:
    """Calculate ROUGE-1, ROUGE-2, and ROUGE-L scores"""
    try:
        from rouge_score import rouge_scorer
        rouge_metrics = {}

        # Use the first response as reference if not provided
        if reference_text is None and len(responses) > 1:
            reference_text = responses.get('real', next(iter(responses.values())))

        if not reference_text:
            rouge_metrics = {}
            for method in responses.keys():
                rouge_metrics.update({
                    f"rouge1_{method}": 0.0,
                    f"rouge2_{method}": 0.0,
                    f"rougel_{method}": 0.0
                })
            return rouge_metrics

        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

        for method, response in responses.items():
            if method == 'real' and reference_text == responses.get('real'):
                # Perfect scores for reference text itself
                rouge_metrics.update({
                    f"rouge1_{method}": 1.0,
                    f"rouge2_{method}": 1.0,
                    f"rougel_{method}": 1.0
                })
                continue

            try:
                scores = scorer.score(reference_text, response)
                rouge_metrics.update({
                    f"rouge1_{method}": scores['rouge1'].fmeasure,
                    f"rouge2_{method}": scores['rouge2'].fmeasure,
                    f"rougel_{method}": scores['rougeL'].fmeasure
                })
            except Exception as e:
                logger.warning(f"ROUGE calculation failed for {method}: {e}")
                rouge_metrics[f"rouge1_{method}"] = 0.0
                rouge_metrics[f"rouge2_{method}"] = 0.0
                rouge_metrics[f"rougel_{method}"] = 0.0

        return rouge_metrics

    except ImportError:
        logger.warning("rouge-score not available for ROUGE calculation")
        rouge_metrics = {}
        for method in responses.keys():
            rouge_metrics.update({
                f"rouge1_{method}": 0.0,
                f"rouge2_{method}": 0.0,
                f"rougel_{method}": 0.0
            })
        return rouge_metrics
    except Exception as e:
        logger.error(f"ROUGE score calculation failed: {e}")
        rouge_metrics = {}
        for method in responses.keys():
            rouge_metrics.update({
                f"rouge1_{method}": 0.0,
                f"rouge2_{method}": 0.0,
                f"rougel_{method}": 0.0
            })
        return rouge_metrics

def calculate_perplexity_score(responses: Dict[str, str]) -> Dict[str, float]:
    """Calculate perplexity score using a simple language model heuristic"""
    try:
        perplexity_scores = {}

        for method, response in responses.items():
            if not response or len(response.strip()) == 0:
                perplexity_scores[f"perplexity_{method}"] = float('inf')
                continue

            words = response.lower().split()
            if len(words) < 2:
                perplexity_scores[f"perplexity_{method}"] = float('inf')
                continue

            # Simple perplexity calculation using word frequency
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Calculate perplexity using unigram model
            total_words = len(words)
            perplexity = 1.0

            for word in words:
                probability = word_counts[word] / total_words
                perplexity *= (1.0 / probability)

            perplexity = perplexity ** (1.0 / total_words)

            # Cap perplexity at reasonable maximum
            perplexity_scores[f"perplexity_{method}"] = min(perplexity, 10000.0)

        return perplexity_scores

    except Exception as e:
        logger.error(f"Perplexity calculation failed: {e}")
        return {f"perplexity_{method}": float('inf') for method in responses.keys()}

def calculate_coherence_score(responses: Dict[str, str]) -> Dict[str, Any]:
    """Calculate coherence score (1-5 scale) using heuristic analysis"""
    try:
        coherence_metrics = {}

        for method, response in responses.items():
            if not response or len(response.strip()) == 0:
                coherence_metrics.update({
                    f"coherence_score_{method}": 1.0,
                    f"coherence_level_{method}": "VERY_LOW"
                })
                continue

            # Heuristic coherence analysis
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            words = response.split()
            score = 3.0  # Base score

            # Length coherence (prefer moderate length responses)
            word_count = len(words)
            if 10 <= word_count <= 100:
                score += 0.5
            elif word_count < 5:
                score -= 1.0
            elif word_count > 200:
                score -= 0.5

            # Sentence structure coherence
            if len(sentences) >= 2:
                score += 0.5  # Multi-sentence responses tend to be more coherent
            elif len(sentences) == 0:
                score -= 1.0

            # Vocabulary diversity (avoid repetition)
            unique_words = len(set(words))
            diversity_ratio = unique_words / max(1, word_count)
            if diversity_ratio > 0.6:
                score += 0.5
            elif diversity_ratio < 0.3:
                score -= 0.5

            # Punctuation coherence
            punctuation_count = sum(1 for char in response if char in '.,!?;:')
            expected_punctuation = max(1, len(sentences) - 1)  # At least one per sentence
            punctuation_ratio = punctuation_count / expected_punctuation
            if 0.5 <= punctuation_ratio <= 2.0:
                score += 0.3
            elif punctuation_ratio < 0.2:
                score -= 0.3

            # Cap score between 1 and 5
            final_score = max(1.0, min(5.0, score))

            # Determine coherence level
            if final_score >= 4.5:
                level = "EXCELLENT"
            elif final_score >= 3.5:
                level = "GOOD"
            elif final_score >= 2.5:
                level = "FAIR"
            elif final_score >= 1.5:
                level = "POOR"
            else:
                level = "VERY_POOR"

            coherence_metrics.update({
                f"coherence_score_{method}": final_score,
                f"coherence_level_{method}": level
            })

        return coherence_metrics

    except Exception as e:
        logger.error(f"Coherence calculation failed: {e}")
        coherence_metrics = {}
        for method in responses.keys():
            coherence_metrics.update({
                f"coherence_score_{method}": 3.0,
                f"coherence_level_{method}": "FAIR"
            })
        return coherence_metrics

def calculate_entropy_score(responses: Dict[str, str]) -> Dict[str, Any]:
    """Calculate comprehensive entropy metrics for text diversity and unpredictability"""
    try:
        entropy_metrics = {}

        for method, response in responses.items():
            if not response or len(response.strip()) == 0:
                entropy_metrics.update({
                    f"entropy_score_{method}": 0.0,
                    f"character_entropy_{method}": 0.0,
                    f"word_entropy_{method}": 0.0,
                    f"text_diversity_{method}": 0.0,
                    f"unpredictability_score_{method}": 0.0
                })
                continue

            # Character-level entropy
            text = response.lower()
            char_counts = {}
            total_chars = len(text)

            for char in text:
                char_counts[char] = char_counts.get(char, 0) + 1

            char_entropy = 0.0
            if total_chars > 0:
                for count in char_counts.values():
                    probability = count / total_chars
                    char_entropy -= probability * math.log2(probability)

            # Normalize character entropy (0-100 scale)
            max_char_entropy = math.log2(256)  # Assuming 256 possible characters
            normalized_char_entropy = (char_entropy / max_char_entropy) * 100.0

            # Word-level entropy
            words = response.split()
            word_counts = {}
            total_words = len(words)

            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            word_entropy = 0.0
            if total_words > 0:
                for count in word_counts.values():
                    probability = count / total_words
                    word_entropy -= probability * math.log2(probability)

            # Normalize word entropy (0-100 scale, assuming max ~15 bits for vocabulary)
            max_word_entropy = math.log2(10000)  # Assuming 10k word vocabulary
            normalized_word_entropy = (word_entropy / max_word_entropy) * 100.0

            # Text diversity score (unique words / total words)
            unique_words = len(word_counts)
            text_diversity = (unique_words / total_words) * 100.0 if total_words > 0 else 0.0

            # Overall unpredictability score (weighted combination)
            unpredictability = (normalized_char_entropy * 0.4 + normalized_word_entropy * 0.4 + text_diversity * 0.2)

            # Determine entropy level
            if unpredictability >= 70:
                entropy_level = "HIGH"
            elif unpredictability >= 40:
                entropy_level = "MEDIUM"
            elif unpredictability >= 10:
                entropy_level = "LOW"
            else:
                entropy_level = "VERY_LOW"

            entropy_metrics.update({
                f"entropy_score_{method}": unpredictability,  # Overall score for backward compatibility
                f"character_entropy_{method}": normalized_char_entropy,
                f"word_entropy_{method}": normalized_word_entropy,
                f"text_diversity_{method}": text_diversity,
                f"unpredictability_score_{method}": unpredictability,
                f"entropy_level_{method}": entropy_level,
                f"unique_words_{method}": unique_words,
                f"total_words_{method}": total_words,
                f"unique_chars_{method}": len(char_counts)
            })

            # Log low entropy warnings (predictable responses might indicate poor anonymization)
            if unpredictability < 20:
                logger.warning(f"ENTROPY ALERT - Method '{method}': Low entropy ({unpredictability:.1f}) - Level: {entropy_level} - Response may be predictable")

        return entropy_metrics

    except Exception as e:
        logger.error(f"Entropy score calculation failed: {e}")
        return {}

def process_batch_texts(config: PIIProtectionConfig, excel_exporter: PIIAnalysisExporter) -> str:
    """
    Process multiple texts from CSV file in batch mode

    Args:
        config: Configuration object
        excel_exporter: Excel exporter instance

    Returns:
        Path to the output Excel file
    """
    try:
        logger.info(f"Starting batch processing from {config.batch_input_file}")

        # Load conditional imports based on batch config
        batch_imports = load_conditional_imports(config)
        logger.info(f"Batch imports loaded: {list(batch_imports.keys())}")

        # Read CSV file
        if not os.path.exists(config.batch_input_file):
            raise FileNotFoundError(f"Input file not found: {config.batch_input_file}")

        df = pd.read_csv(config.batch_input_file)

        if config.batch_text_column not in df.columns:
            raise ValueError(f"Text column '{config.batch_text_column}' not found in CSV. Available columns: {list(df.columns)}")

        # Limit rows if specified
        if config.batch_max_rows > 0:
            df = df.head(config.batch_max_rows)

        total_rows = len(df)
        logger.info(f"Processing {total_rows} rows from CSV")

        # Initialize required models for batch processing
        batch_nlp = None
        if config.enable_fake_names or config.enable_xxxx_masking:
            try:
                import spacy
                batch_nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model for batch processing")
            except OSError:
                logger.error("spaCy model 'en_core_web_sm' not found. NER features will be disabled in batch mode.")
                batch_nlp = None

        processed_count = 0

        for idx, row in df.iterrows():
            try:
                user_prompt = str(row[config.batch_text_column]).strip()
                if not user_prompt:
                    continue

                logger.info(f"Processing row {idx + 1}/{total_rows}")

                # Initialize data structures for this text
                responses = {}
                prompts = {}
                processing_times = {}
                mappings = {}

                # Process real names (baseline) if enabled
                if config.enable_real_names:
                    try:
                        start_time = time.time()
                        response_real = model.generate_content(user_prompt)
                        processing_times['real'] = time.time() - start_time
                        responses['real'] = response_real.text
                        prompts['real'] = user_prompt
                    except Exception as e:
                        logger.error(f"Real names processing failed for row {idx + 1}: {e}")
                        responses['real'] = f"Error: {str(e)}"
                        prompts['real'] = user_prompt

                # Process fake names if enabled
                if config.enable_fake_names:
                    try:
                        start_time = time.time()
                        fake_prompt, ner_map = fake_ner_replace(user_prompt, batch_nlp, config, batch_imports)
                        prompts['fake'] = fake_prompt
                        mappings['ner_mapping'] = ner_map

                        response_fake = model.generate_content(fake_prompt)
                        bot_reply_fake = restore_fake_ner(response_fake.text, ner_map)
                        processing_times['fake'] = time.time() - start_time
                        responses['fake'] = bot_reply_fake
                    except Exception as e:
                        logger.error(f"Fake names processing failed for row {idx + 1}: {e}")
                        responses['fake'] = f"Error: {str(e)}"
                        prompts['fake'] = fake_prompt if 'fake_prompt' in locals() else user_prompt

                # Process XXXX masking if enabled
                if config.enable_xxxx_masking:
                    try:
                        start_time = time.time()
                        masked_prompt, mask_map = mask_ner_with_xxxx(user_prompt, batch_nlp, config, batch_imports)
                        prompts['masked'] = masked_prompt
                        mappings['mask_mapping'] = mask_map

                        response_mask = model.generate_content(masked_prompt)
                        bot_reply_mask = response_mask.text.replace("XXXX", ", ".join(mask_map.values()))
                        processing_times['masked'] = time.time() - start_time
                        responses['masked'] = bot_reply_mask
                    except Exception as e:
                        logger.error(f"XXXX masking processing failed for row {idx + 1}: {e}")
                        responses['masked'] = f"Error: {str(e)}"
                        prompts['masked'] = masked_prompt if 'masked_prompt' in locals() else user_prompt

                # Process LLM-based PII removal if enabled
                if config.enable_llm_pii_removal and 'llm_pii_remover' in imports:
                    try:
                        start_time = time.time()
                        llm_anonymized_prompt = imports['llm_pii_remover'](user_prompt)
                        prompts['llm'] = llm_anonymized_prompt

                        response_llm = model.generate_content(llm_anonymized_prompt)
                        processing_times['llm'] = time.time() - start_time
                        responses['llm'] = response_llm.text
                    except Exception as e:
                        logger.error(f"LLM PII removal processing failed for row {idx + 1}: {e}")
                        responses['llm'] = f"Error: {str(e)}"
                        prompts['llm'] = llm_anonymized_prompt if 'llm_anonymized_prompt' in locals() else user_prompt

                # Calculate metrics if responses exist
                similarities = {}
                deepeval_scores = {}
                pii_scores = {}
                pii_leakage_rates = {}
                detailed_plr_metrics = {}
                reidentification_scores = {}
                entropy_scores = {}
                bleu_scores = {}
                rouge_scores = {}
                perplexity_scores = {}
                coherence_scores = {}

                if responses:
                    try:
                        similarities = calculate_semantic_similarity(responses)
                    except Exception as e:
                        logger.error(f"Semantic similarity failed for row {idx + 1}: {e}")

                    try:
                        prompts_responses = {method: (prompts.get(method, user_prompt), response)
                                           for method, response in responses.items()}
                        deepeval_scores = calculate_deepeval_scores(prompts_responses)
                    except Exception as e:
                        logger.error(f"DeepEval failed for row {idx + 1}: {e}")

                    if config.enable_real_names and config.enable_pii_leakage_detection:
                        try:
                            pii_scores = calculate_pii_leakage(user_prompt, responses, batch_nlp)
                            pii_leakage_rates = calculate_pii_leakage_rate(user_prompt, responses, batch_nlp)
                            detailed_plr_metrics = calculate_detailed_pii_leakage_rate(user_prompt, responses, batch_nlp)
                            reidentification_scores = calculate_reidentification_risk(user_prompt, responses, batch_nlp)
                        except Exception as e:
                            logger.error(f"PII leakage failed for row {idx + 1}: {e}")

                    try:
                        entropy_scores = calculate_entropy_score(responses)
                    except Exception as e:
                        logger.error(f"Entropy score calculation failed for row {idx + 1}: {e}")

                    try:
                        bleu_scores = calculate_bleu_score(responses, user_prompt)
                    except Exception as e:
                        logger.error(f"BLEU score calculation failed for row {idx + 1}: {e}")

                    try:
                        rouge_scores = calculate_rouge_scores(responses, user_prompt)
                    except Exception as e:
                        logger.error(f"ROUGE score calculation failed for row {idx + 1}: {e}")

                    try:
                        perplexity_scores = calculate_perplexity_score(responses)
                    except Exception as e:
                        logger.error(f"Perplexity calculation failed for row {idx + 1}: {e}")

                    try:
                        coherence_scores = calculate_coherence_score(responses)
                    except Exception as e:
                        logger.error(f"Coherence calculation failed for row {idx + 1}: {e}")

                # Prepare analysis data
                analysis_data = {
                    'batch_row_id': idx + 1,
                    'original_prompt': user_prompt,
                    **{f'{method}_prompt': prompts.get(method, user_prompt) for method in responses.keys()},
                    **{f'{method}_response': response for method, response in responses.items()},
                    **mappings,
                    **deepeval_scores,
                    **similarities,
                    **pii_scores,
                    **pii_leakage_rates,
                    **detailed_plr_metrics,
                    **reidentification_scores,
                    **entropy_scores,
                    **bleu_scores,
                    **rouge_scores,
                    **perplexity_scores,
                    **coherence_scores,
                    **{f'processing_time_{method}': time_val for method, time_val in processing_times.items()},
                    'entities_detected': len([ent for ent in batch_nlp(user_prompt).ents
                                            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]]) if batch_nlp else 0
                }

                # Add original CSV data for reference
                for col in df.columns:
                    if col != config.batch_text_column:
                        analysis_data[f'original_{col}'] = row[col]

                excel_exporter.add_analysis_record(analysis_data)
                processed_count += 1

                # Progress logging
                if (idx + 1) % 10 == 0:
                    logger.info(f"Processed {idx + 1}/{total_rows} rows")

            except Exception as e:
                logger.error(f"Failed to process row {idx + 1}: {e}")
                continue

        # Export final results
        output_path = excel_exporter.export_to_excel(config.batch_output_file)
        logger.info(f"Batch processing completed. Processed {processed_count}/{total_rows} rows. Output: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise

# Main application logic
def main():
    """Main application logic with modular processing"""

    # Check for batch processing mode
    if config.enable_batch_processing:
        if config.batch_background_mode:
            # Run in background mode without UI
            logger.info("Running in batch processing background mode")
            try:
                output_path = process_batch_texts(config, excel_exporter)
                logger.info(f"Batch processing completed successfully. Output: {output_path}")
                print(f"Batch processing completed. Results saved to: {output_path}")
                return
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                print(f"Batch processing failed: {e}")
                return
        else:
            # Show batch processing UI
            st.title("🔄 Batch Processing Mode")
            st.markdown("Process multiple texts from CSV file")

            if st.button("🚀 Start Batch Processing"):
                with st.spinner("Processing batch texts... This may take a while."):
                    try:
                        output_path = process_batch_texts(config, excel_exporter)
                        st.success(f"✅ Batch processing completed! Results saved to: {output_path}")

                        # Show summary
                        stats = excel_exporter.get_current_stats()
                        st.info(f"📊 Processed {stats['total_queries']} texts")

                    except Exception as e:
                        st.error(f"❌ Batch processing failed: {str(e)}")
                        logger.error(f"Batch processing failed: {e}")

            # Show current configuration
            if config.show_debug_info:
                with st.expander("🔧 Batch Configuration", expanded=False):
                    batch_config = {
                        'input_file': config.batch_input_file,
                        'text_column': config.batch_text_column,
                        'max_rows': config.batch_max_rows,
                        'output_file': config.batch_output_file,
                        'background_mode': config.batch_background_mode
                    }
                    st.json(batch_config)

            return

    # Display current configuration
    if config.show_debug_info:
        with st.expander("🔧 Current Configuration", expanded=False):
            st.json(config.to_dict())
    
    # Chat input
    user_prompt = st.chat_input("Ask me anything...")
    
    if user_prompt:
        st.session_state.query_count += 1
        
        # Initialize data structures
        responses = {}
        prompts = {}
        processing_times = {}
        mappings = {}
        
        # Process real names (baseline) if enabled
        response_real = None
        if config.enable_real_names:
            st.subheader("🔴 LLM Response with Real Names (Baseline)")
            st.chat_message("user").markdown(user_prompt)

            try:
                if config.enable_performance_timing:
                    start_time = time.time()

                response_real = model.generate_content(user_prompt)

                if config.enable_performance_timing:
                    processing_times['real'] = time.time() - start_time

                st.chat_message("assistant").markdown(response_real.text)
                responses['real'] = response_real.text
                prompts['real'] = user_prompt
            except Exception as e:
                st.error(f"❌ Error generating real names response: {str(e)}")
                logger.error(f"Real names processing failed: {e}")
                responses['real'] = f"Error: {str(e)}"
                prompts['real'] = user_prompt
        
        # Process fake names if enabled
        if config.enable_fake_names:
            st.subheader("🟡 LLM Response with Fake Names")

            try:
                if config.enable_performance_timing:
                    start_time = time.time()

                fake_prompt, ner_map = fake_ner_replace(user_prompt, nlp)
                prompts['fake'] = fake_prompt
                mappings['ner_mapping'] = ner_map

                st.chat_message("user").markdown(fake_prompt)

                if config.show_mappings and ner_map:
                    st.info(f"**Fake NER mapping:** {ner_map}")

                response_fake = model.generate_content(fake_prompt)
                bot_reply_fake = restore_fake_ner(response_fake.text, ner_map)

                if config.enable_performance_timing:
                    processing_times['fake'] = time.time() - start_time

                st.chat_message("assistant").markdown(bot_reply_fake)
                responses['fake'] = bot_reply_fake
            except Exception as e:
                st.error(f"❌ Error generating fake names response: {str(e)}")
                logger.error(f"Fake names processing failed: {e}")
                responses['fake'] = f"Error: {str(e)}"
                prompts['fake'] = fake_prompt if 'fake_prompt' in locals() else user_prompt
        
        # Process XXXX masking if enabled
        if config.enable_xxxx_masking:
            st.subheader("🔵 LLM Response with XXXX Masking")

            try:
                if config.enable_performance_timing:
                    start_time = time.time()

                masked_prompt, mask_map = mask_ner_with_xxxx(user_prompt, nlp)
                prompts['masked'] = masked_prompt
                mappings['mask_mapping'] = mask_map

                st.chat_message("user").markdown(masked_prompt)

                if config.show_mappings and mask_map:
                    st.info(f"**XXXX Mask mapping:** {mask_map}")

                response_mask = model.generate_content(masked_prompt)
                bot_reply_mask = response_mask.text.replace("XXXX", ", ".join(mask_map.values()))

                if config.enable_performance_timing:
                    processing_times['masked'] = time.time() - start_time

                st.chat_message("assistant").markdown(bot_reply_mask)
                responses['masked'] = bot_reply_mask
            except Exception as e:
                st.error(f"❌ Error generating masked response: {str(e)}")
                logger.error(f"Masked processing failed: {e}")
                responses['masked'] = f"Error: {str(e)}"
                prompts['masked'] = masked_prompt if 'masked_prompt' in locals() else user_prompt
        
        # Process LLM-based PII removal if enabled
        if config.enable_llm_pii_removal and 'llm_pii_remover' in imports:
            st.subheader("🟢 LLM Response with LLM-based PII Removal")

            try:
                if config.enable_performance_timing:
                    start_time = time.time()

                llm_anonymized_prompt = imports['llm_pii_remover'](user_prompt)
                prompts['llm'] = llm_anonymized_prompt

                st.chat_message("user").markdown(llm_anonymized_prompt)

                response_llm = model.generate_content(llm_anonymized_prompt)

                if config.enable_performance_timing:
                    processing_times['llm'] = time.time() - start_time

                st.chat_message("assistant").markdown(response_llm.text)
                responses['llm'] = response_llm.text
            except Exception as e:
                st.error(f"❌ Error generating LLM-based PII removal response: {str(e)}")
                logger.error(f"LLM PII removal processing failed: {e}")
                responses['llm'] = f"Error: {str(e)}"
                prompts['llm'] = llm_anonymized_prompt if 'llm_anonymized_prompt' in locals() else user_prompt
        
        # Calculate metrics only if there are responses to analyze
        if responses:
            st.markdown("---")
            st.subheader("📊 Analysis Results")

            # Semantic similarity
            try:
                similarities = calculate_semantic_similarity(responses)
            except Exception as e:
                st.warning(f"⚠️ Semantic similarity calculation failed: {str(e)}")
                logger.error(f"Semantic similarity failed: {e}")
                similarities = {}

            # DeepEval scores
            try:
                prompts_responses = {method: (prompts.get(method, user_prompt), response)
                                   for method, response in responses.items()}
                deepeval_scores = calculate_deepeval_scores(prompts_responses)
            except Exception as e:
                st.warning(f"⚠️ DeepEval calculation failed: {str(e)}")
                logger.error(f"DeepEval failed: {e}")
                deepeval_scores = {}

            # PII leakage (only if real names are enabled for comparison)
            pii_scores = {}
            pii_leakage_rates = {}
            detailed_plr_metrics = {}
            reidentification_scores = {}
            entropy_scores = {}
            bleu_scores = {}
            rouge_scores = {}
            perplexity_scores = {}
            coherence_scores = {}
            if config.enable_real_names and config.enable_pii_leakage_detection:
                try:
                    pii_scores = calculate_pii_leakage(user_prompt, responses, nlp)
                    pii_leakage_rates = calculate_pii_leakage_rate(user_prompt, responses, nlp)
                    detailed_plr_metrics = calculate_detailed_pii_leakage_rate(user_prompt, responses, nlp)
                    reidentification_scores = calculate_reidentification_risk(user_prompt, responses, nlp)
                except Exception as e:
                    st.warning(f"⚠️ PII leakage calculation failed: {str(e)}")
                    logger.error(f"PII leakage failed: {e}")
                    pii_scores = {}
                    pii_leakage_rates = {}
                    detailed_plr_metrics = {}
                    reidentification_scores = {}

            try:
                entropy_scores = calculate_entropy_score(responses)
            except Exception as e:
                st.warning(f"⚠️ Entropy score calculation failed: {str(e)}")
                logger.error(f"Entropy score failed: {e}")
                entropy_scores = {}

            try:
                bleu_scores = calculate_bleu_score(responses, user_prompt)
            except Exception as e:
                st.warning(f"⚠️ BLEU score calculation failed: {str(e)}")
                logger.error(f"BLEU score failed: {e}")
                bleu_scores = {}

            try:
                rouge_scores = calculate_rouge_scores(responses, user_prompt)
            except Exception as e:
                st.warning(f"⚠️ ROUGE score calculation failed: {str(e)}")
                logger.error(f"ROUGE score failed: {e}")
                rouge_scores = {}

            try:
                perplexity_scores = calculate_perplexity_score(responses)
            except Exception as e:
                st.warning(f"⚠️ Perplexity calculation failed: {str(e)}")
                logger.error(f"Perplexity failed: {e}")
                perplexity_scores = {}

            try:
                coherence_scores = calculate_coherence_score(responses)
            except Exception as e:
                st.warning(f"⚠️ Coherence calculation failed: {str(e)}")
                logger.error(f"Coherence failed: {e}")
                coherence_scores = {}

            # Display metrics
            col1, col2 = st.columns(2)

            with col1:
                if deepeval_scores:
                    st.markdown("**🎯 DeepEval Answer Relevancy:**")
                    for method in responses.keys():
                        score = deepeval_scores.get(f"relevancy_{method}", 0.0)
                        st.write(f"• {method.title()}: {score:.3f}")

                if similarities:
                    st.markdown("**🧠 Semantic Similarity:**")
                    for sim_key, score in similarities.items():
                        clean_key = sim_key.replace('similarity_', '').replace('_', ' vs ').title()
                        st.write(f"• {clean_key}: {score:.3f}")

            with col2:
                if pii_scores:
                    st.markdown("**🔒 PII Leakage Detection:**")
                    for method in responses.keys():
                        leakage = pii_scores.get(f"pii_leakage_{method}", 0)
                        f1 = pii_scores.get(f"f1_{method}", 0)
                        st.write(f"• {method.title()}: {leakage} leaked, F1: {f1}")

                if pii_leakage_rates:
                    st.markdown("**📊 PII Leakage Rate (PLR) (%):**")
                    for method in responses.keys():
                        rate = pii_leakage_rates.get(f"pii_leakage_rate_{method}", 0.0)
                        severity = detailed_plr_metrics.get(f"pii_leakage_severity_{method}", "UNKNOWN")
                        severity_icon = {"NONE": "✅", "LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴", "CRITICAL": "🚨"}.get(severity, "❓")
                        st.write(f"• {method.title()}: {rate:.1f}% {severity_icon} ({severity})")

                if detailed_plr_metrics:
                    # Show per-entity-type leakage if available
                    entity_types = ["person", "org", "gpe", "email", "phone"]
                    entity_type_names = {"person": "Names", "org": "Orgs", "gpe": "Locations", "email": "Emails", "phone": "Phones"}

                    for entity_type in entity_types:
                        rates = []
                        for method in responses.keys():
                            rate_key = f"{entity_type}_leakage_rate_{method}"
                            if rate_key in detailed_plr_metrics:
                                rates.append((method, detailed_plr_metrics[rate_key]))

                        if rates and any(rate > 0 for _, rate in rates):
                            st.markdown(f"**{entity_type_names[entity_type]} PLR:**")
                            for method, rate in rates:
                                if rate > 0:
                                    st.write(f"• {method.title()}: {rate:.1f}%")
                            break  # Only show first entity type with leakage

                if reidentification_scores:
                    st.markdown("**🎯 Re-identification Risk (%):**")
                    for method in responses.keys():
                        risk = reidentification_scores.get(f"reidentification_risk_{method}", 0.0)
                        risk_level = reidentification_scores.get(f"reidentification_risk_level_{method}", "UNKNOWN")
                        risk_icon = {"NONE": "✅", "LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴", "CRITICAL": "🚨"}.get(risk_level, "❓")
                        st.write(f"• {method.title()}: {risk:.1f}% {risk_icon} ({risk_level})")

                if entropy_scores:
                    st.markdown("**🧬 Entropy Score (Unpredictability):**")
                    for method in responses.keys():
                        entropy = entropy_scores.get(f"entropy_score_{method}", 0.0)
                        entropy_level = entropy_scores.get(f"entropy_level_{method}", "UNKNOWN")
                        entropy_icon = {"VERY_LOW": "🔴", "LOW": "🟠", "MEDIUM": "🟡", "HIGH": "🟢"}.get(entropy_level, "❓")
                        st.write(f"• {method.title()}: {entropy:.1f} {entropy_icon} ({entropy_level})")

                        # Show detailed entropy breakdown if available
                        char_entropy = entropy_scores.get(f"character_entropy_{method}", 0.0)
                        word_entropy = entropy_scores.get(f"word_entropy_{method}", 0.0)
                        diversity = entropy_scores.get(f"text_diversity_{method}", 0.0)
                        if char_entropy > 0 or word_entropy > 0:
                            with st.expander(f"Detailed Entropy for {method.title()}", expanded=False):
                                st.write(f"• Character Entropy: {char_entropy:.1f}")
                                st.write(f"• Word Entropy: {word_entropy:.1f}")
                                st.write(f"• Text Diversity: {diversity:.1f}%")

                # NLP Quality Metrics
                if bleu_scores or rouge_scores or perplexity_scores or coherence_scores:
                    st.markdown("**📝 NLP Quality Metrics:**")

                    if bleu_scores:
                        st.markdown("**BLEU Score:**")
                        for method in responses.keys():
                            bleu = bleu_scores.get(f"bleu_score_{method}", 0.0)
                            st.write(f"• {method.title()}: {bleu:.3f}")

                    if rouge_scores:
                        st.markdown("**ROUGE Scores:**")
                        for method in responses.keys():
                            rouge1 = rouge_scores.get(f"rouge1_{method}", 0.0)
                            rouge2 = rouge_scores.get(f"rouge2_{method}", 0.0)
                            rougel = rouge_scores.get(f"rougel_{method}", 0.0)
                            st.write(f"• {method.title()}: R1={rouge1:.3f}, R2={rouge2:.3f}, RL={rougel:.3f}")

                    if perplexity_scores:
                        st.markdown("**Perplexity:**")
                        for method in responses.keys():
                            perplexity = perplexity_scores.get(f"perplexity_{method}", float('inf'))
                            perplexity_display = ".1f" if perplexity != float('inf') else "∞"
                            st.write(f"• {method.title()}: {perplexity_display}")

                    if coherence_scores:
                        st.markdown("**Coherence (1-5):**")
                        for method in responses.keys():
                            coherence = coherence_scores.get(f"coherence_score_{method}", 3.0)
                            coherence_level = coherence_scores.get(f"coherence_level_{method}", "FAIR")
                            coherence_icon = {"VERY_POOR": "🔴", "POOR": "🟠", "FAIR": "🟡", "GOOD": "🟢", "EXCELLENT": "🟢"}.get(coherence_level, "❓")
                            st.write(f"• {method.title()}: {coherence:.1f}/5 {coherence_icon} ({coherence_level})")

                if processing_times and config.show_processing_times:
                    st.markdown("**⏱️ Processing Times:**")
                    for method, time_taken in processing_times.items():
                        st.write(f"• {method.title()}: {time_taken:.3f}s")
        else:
            st.warning("⚠️ No PII protection methods are enabled. Please enable at least one method in the sidebar.")
        
        # Excel export
        if config.enable_excel_export and excel_exporter and responses:
            try:
                # Prepare comprehensive data
                analysis_data = {
                    'original_prompt': user_prompt,
                    **{f'{method}_prompt': prompts.get(method, user_prompt) for method in responses.keys()},
                    **{f'{method}_response': response for method, response in responses.items()},
                    **mappings,
                    **deepeval_scores,
                    **similarities,
                    **pii_scores,
                    **pii_leakage_rates,
                    **detailed_plr_metrics,
                    **reidentification_scores,
                    **entropy_scores,
                    **bleu_scores,
                    **rouge_scores,
                    **perplexity_scores,
                    **coherence_scores,
                    **{f'processing_time_{method}': time_val for method, time_val in processing_times.items()},
                    'entities_detected': len([ent for ent in nlp(user_prompt).ents
                                            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]]) if nlp else 0
                }

                excel_exporter.add_analysis_record(analysis_data)

                # Auto export if enabled
                if config.auto_export and st.session_state.query_count % config.export_batch_size == 0:
                    filepath = excel_exporter.export_to_excel()
                    if filepath:
                        st.success(f"📊 Auto-exported data to: {filepath}")

                # Export controls
                st.markdown("---")
                st.subheader("📊 Data Export")

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("📥 Export to Excel"):
                        filepath = excel_exporter.export_to_excel()
                        if filepath:
                            st.success(f"✅ Data exported to: {filepath}")
                            stats = excel_exporter.get_current_stats()
                            st.info(f"📈 Total queries: {stats['total_queries']}")

                with col2:
                    if st.button("📈 Show Stats"):
                        stats = excel_exporter.get_current_stats()
                        if stats['total_queries'] > 0:
                            st.success(f"📊 Statistics for {stats['total_queries']} processed queries:")
                            col_stats1, col_stats2, col_stats3 = st.columns(3)

                            with col_stats1:
                                st.markdown("**🎯 Average Relevancy Scores:**")
                                st.write(f"• Real Names: {stats.get('avg_relevancy_real', 0):.3f}")
                                st.write(f"• Fake Names: {stats.get('avg_relevancy_fake', 0):.3f}")
                                st.write(f"• XXXX Masking: {stats.get('avg_relevancy_masked', 0):.3f}")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_relevancy_llm', 0):.3f}")

                                st.markdown("**🧠 Average Semantic Similarity:**")
                                st.write(f"• Real vs Fake: {stats.get('avg_similarity_real_fake', 0):.3f}")
                                st.write(f"• Real vs Masked: {stats.get('avg_similarity_real_masked', 0):.3f}")
                                st.write(f"• Real vs LLM: {stats.get('avg_similarity_real_llm', 0):.3f}")

                            with col_stats2:
                                st.markdown("**🔒 Average PII Leakage Rate (PLR) (%):**")
                                st.write(f"• Real Names: {stats.get('avg_pii_leakage_rate_real', 0):.1f}%")
                                st.write(f"• Fake Names: {stats.get('avg_pii_leakage_rate_fake', 0):.1f}%")
                                st.write(f"• XXXX Masking: {stats.get('avg_pii_leakage_rate_masked', 0):.1f}%")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_pii_leakage_rate_llm', 0):.1f}%")

                                # Show PLR severity summary
                                plr_severities = []
                                for method in ['real', 'fake', 'masked', 'llm']:
                                    severity_key = f'most_common_plr_severity_{method}'
                                    if severity_key in stats:
                                        plr_severities.append(f"{method.title()}: {stats[severity_key]}")

                                if plr_severities:
                                    st.markdown("**🚨 PLR Severity Summary:**")
                                    for severity_info in plr_severities:
                                        st.write(f"• {severity_info}")

                                st.markdown("**🎯 Average Re-identification Risk (%):**")
                                st.write(f"• Real Names: {stats.get('avg_reidentification_risk_real', 0):.1f}%")
                                st.write(f"• Fake Names: {stats.get('avg_reidentification_risk_fake', 0):.1f}%")
                                st.write(f"• XXXX Masking: {stats.get('avg_reidentification_risk_masked', 0):.1f}%")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_reidentification_risk_llm', 0):.1f}%")

                                # Show Re-ID risk level summary
                                reid_levels = []
                                for method in ['real', 'fake', 'masked', 'llm']:
                                    level_key = f'most_common_reid_risk_level_{method}'
                                    if level_key in stats:
                                        reid_levels.append(f"{method.title()}: {stats[level_key]}")

                                if reid_levels:
                                    st.markdown("**🚨 Re-ID Risk Level Summary:**")
                                    for level_info in reid_levels:
                                        st.write(f"• {level_info}")

                            with col_stats3:
                                st.markdown("**🧬 Average Entropy Score (Unpredictability):**")
                                st.write(f"• Real Names: {stats.get('avg_entropy_score_real', 0):.1f}")
                                st.write(f"• Fake Names: {stats.get('avg_entropy_score_fake', 0):.1f}")
                                st.write(f"• XXXX Masking: {stats.get('avg_entropy_score_masked', 0):.1f}")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_entropy_score_llm', 0):.1f}")

                                # Show Entropy level summary
                                entropy_levels = []
                                for method in ['real', 'fake', 'masked', 'llm']:
                                    level_key = f'most_common_entropy_level_{method}'
                                    if level_key in stats:
                                        entropy_levels.append(f"{method.title()}: {stats[level_key]}")

                                if entropy_levels:
                                    st.markdown("**🧬 Entropy Level Summary:**")
                                    for level_info in entropy_levels:
                                        st.write(f"• {level_info}")

                                st.markdown("**⏱️ Average Processing Times (seconds):**")
                                st.write(f"• Real Names: {stats.get('avg_processing_time_real', 0):.3f}")
                                st.write(f"• Fake Names: {stats.get('avg_processing_time_fake', 0):.3f}")
                                st.write(f"• XXXX Masking: {stats.get('avg_processing_time_masked', 0):.3f}")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_processing_time_llm', 0):.3f}")

                                st.markdown("**📈 Session Summary:**")
                                st.write(f"• Total Queries: {stats['total_queries']}")
                        else:
                            st.info("📊 No queries processed yet. Submit a query to see statistics.")

                with col3:
                    if st.button("🗑️ Clear Data"):
                        excel_exporter.clear_data()
                        st.success("✅ Data cleared!")
            except Exception as e:
                st.error(f"❌ Excel export failed: {str(e)}")
                logger.error(f"Excel export failed: {e}")

if __name__ == "__main__":
    main()
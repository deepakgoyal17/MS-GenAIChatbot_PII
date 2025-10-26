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

def calculate_reidentification_risk(original_prompt: str, responses: Dict[str, str], nlp_model=None) -> Dict[str, float]:
    """Calculate re-identification risk based on unique entity combinations"""
    if not config.enable_pii_leakage_detection or nlp_model is None:
        return {}

    try:
        doc = nlp_model(original_prompt)
        real_entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]

        if len(real_entities) < 2:
            return {f"reidentification_risk_{method}": 0.0 for method in responses.keys()}

        reidentification_scores = {}
        for method, response in responses.items():
            response_doc = nlp_model(response)
            response_entities = [(ent.text, ent.label_) for ent in response_doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EMAIL", "PHONE"]]

            # Calculate how many unique entity combinations are preserved
            preserved_combinations = 0
            total_combinations = len(real_entities) * (len(real_entities) - 1) // 2

            if total_combinations > 0:
                for i, (ent1, label1) in enumerate(real_entities):
                    for j, (ent2, label2) in enumerate(real_entities[i+1:], i+1):
                        # Check if both entities appear in response (simplified re-identification risk)
                        ent1_present = any(ent1 in resp_ent[0] for resp_ent in response_entities)
                        ent2_present = any(ent2 in resp_ent[0] for resp_ent in response_entities)
                        if ent1_present and ent2_present:
                            preserved_combinations += 1

                reidentification_scores[f"reidentification_risk_{method}"] = (preserved_combinations / total_combinations) * 100.0
            else:
                reidentification_scores[f"reidentification_risk_{method}"] = 0.0

        return reidentification_scores

    except Exception as e:
        logger.error(f"Re-identification risk calculation failed: {e}")
        return {}

def calculate_entropy_score(responses: Dict[str, str]) -> Dict[str, float]:
    """Calculate entropy score based on text diversity"""
    try:
        entropy_scores = {}

        for method, response in responses.items():
            if not response or len(response.strip()) == 0:
                entropy_scores[f"entropy_score_{method}"] = 0.0
                continue

            # Calculate character-level entropy
            text = response.lower()
            char_counts = {}
            total_chars = len(text)

            for char in text:
                char_counts[char] = char_counts.get(char, 0) + 1

            entropy = 0.0
            for count in char_counts.values():
                probability = count / total_chars
                entropy -= probability * math.log2(probability)

            # Normalize entropy (max entropy for ASCII is ~7 bits, but we'll scale to 0-100)
            max_entropy = math.log2(256)  # Assuming 256 possible characters
            normalized_entropy = (entropy / max_entropy) * 100.0

            entropy_scores[f"entropy_score_{method}"] = normalized_entropy

        return entropy_scores

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
                reidentification_scores = {}
                entropy_scores = {}

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
                            reidentification_scores = calculate_reidentification_risk(user_prompt, responses, batch_nlp)
                        except Exception as e:
                            logger.error(f"PII leakage failed for row {idx + 1}: {e}")

                    try:
                        entropy_scores = calculate_entropy_score(responses)
                    except Exception as e:
                        logger.error(f"Entropy score calculation failed for row {idx + 1}: {e}")

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
                    **reidentification_scores,
                    **entropy_scores,
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
            reidentification_scores = {}
            entropy_scores = {}
            if config.enable_real_names and config.enable_pii_leakage_detection:
                try:
                    pii_scores = calculate_pii_leakage(user_prompt, responses, nlp)
                    pii_leakage_rates = calculate_pii_leakage_rate(user_prompt, responses, nlp)
                    reidentification_scores = calculate_reidentification_risk(user_prompt, responses, nlp)
                except Exception as e:
                    st.warning(f"⚠️ PII leakage calculation failed: {str(e)}")
                    logger.error(f"PII leakage failed: {e}")
                    pii_scores = {}
                    pii_leakage_rates = {}
                    reidentification_scores = {}

            try:
                entropy_scores = calculate_entropy_score(responses)
            except Exception as e:
                st.warning(f"⚠️ Entropy score calculation failed: {str(e)}")
                logger.error(f"Entropy score failed: {e}")
                entropy_scores = {}

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
                    st.markdown("**📊 PII Leakage Rate (%):**")
                    for method in responses.keys():
                        rate = pii_leakage_rates.get(f"pii_leakage_rate_{method}", 0.0)
                        st.write(f"• {method.title()}: {rate:.1f}%")

                if reidentification_scores:
                    st.markdown("**🎯 Re-identification Risk (%):**")
                    for method in responses.keys():
                        risk = reidentification_scores.get(f"reidentification_risk_{method}", 0.0)
                        st.write(f"• {method.title()}: {risk:.1f}%")

                if entropy_scores:
                    st.markdown("**🧬 Entropy Score:**")
                    for method in responses.keys():
                        entropy = entropy_scores.get(f"entropy_score_{method}", 0.0)
                        st.write(f"• {method.title()}: {entropy:.1f}")

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
                    **reidentification_scores,
                    **entropy_scores,
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
                                st.markdown("**🔒 Average PII Leakage Rate (%):**")
                                st.write(f"• Real Names: {stats.get('avg_pii_leakage_rate_real', 0):.1f}%")
                                st.write(f"• Fake Names: {stats.get('avg_pii_leakage_rate_fake', 0):.1f}%")
                                st.write(f"• XXXX Masking: {stats.get('avg_pii_leakage_rate_masked', 0):.1f}%")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_pii_leakage_rate_llm', 0):.1f}%")

                                st.markdown("**🎯 Average Re-identification Risk (%):**")
                                st.write(f"• Real Names: {stats.get('avg_reidentification_risk_real', 0):.1f}%")
                                st.write(f"• Fake Names: {stats.get('avg_reidentification_risk_fake', 0):.1f}%")
                                st.write(f"• XXXX Masking: {stats.get('avg_reidentification_risk_masked', 0):.1f}%")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_reidentification_risk_llm', 0):.1f}%")

                            with col_stats3:
                                st.markdown("**🧬 Average Entropy Score:**")
                                st.write(f"• Real Names: {stats.get('avg_entropy_score_real', 0):.1f}")
                                st.write(f"• Fake Names: {stats.get('avg_entropy_score_fake', 0):.1f}")
                                st.write(f"• XXXX Masking: {stats.get('avg_entropy_score_masked', 0):.1f}")
                                st.write(f"• LLM-based PII Removal: {stats.get('avg_entropy_score_llm', 0):.1f}")

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
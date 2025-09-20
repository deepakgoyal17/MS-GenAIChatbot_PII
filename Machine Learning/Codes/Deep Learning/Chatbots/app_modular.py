#!/usr/bin/env python3
"""
Modular PII Protection Chatbot with Feature Flags
Enhanced version with configurable features
"""

import os
import warnings
import time
import re
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
api_key = os.getenv("GOOGLE-API-KEY")
if not api_key:
    st.error("⚠️ **API Key Missing**: GOOGLE-API-KEY not found in environment variables.")
    st.info("Please add your Google API key to the .env file: GOOGLE-API-KEY=your_key_here")
    st.stop()

# Configure Gemini AI
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

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
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.model_name = "gemini-1.5-flash"

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

def fake_ner_replace(text: str) -> Tuple[str, Dict[str, str]]:
    """Replace PII with fake data"""
    if not config.enable_fake_names or nlp is None or 'faker' not in imports:
        return text, {}
    
    try:
        # Apply smart capitalization if enabled
        if config.enable_capitalization:
            text = smart_capitalize(text)
        
        doc = nlp(text)
        faker = imports['faker']
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
        if config.enable_regex_fallback:
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

def mask_ner_with_xxxx(text: str) -> Tuple[str, Dict[str, str]]:
    """Mask PII with XXXX"""
    if not config.enable_xxxx_masking or nlp is None:
        return text, {}
    
    try:
        # Apply smart capitalization if enabled
        if config.enable_capitalization:
            text = smart_capitalize(text)
        
        doc = nlp(text)
        mask_map = {}
        masked_text = text
        
        # Process spaCy entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]:
                mask_map[f"XXXX_{len(mask_map)}"] = ent.text
                masked_text = masked_text.replace(ent.text, "XXXX")
        
        # Regex fallback if enabled
        if config.enable_regex_fallback:
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

def calculate_pii_leakage(original_prompt: str, responses: Dict[str, str]) -> Dict[str, int]:
    """Calculate PII leakage scores"""
    if not config.enable_pii_leakage_detection or nlp is None:
        return {}
    
    try:
        doc = nlp(original_prompt)
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

# Main application logic
def main():
    """Main application logic with modular processing"""
    
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

            if config.enable_performance_timing:
                start_time = time.time()

            response_real = model.generate_content(user_prompt)

            if config.enable_performance_timing:
                processing_times['real'] = time.time() - start_time

            st.chat_message("assistant").markdown(response_real.text)
            responses['real'] = response_real.text
            prompts['real'] = user_prompt
        
        # Process fake names if enabled
        if config.enable_fake_names:
            st.subheader("🟡 LLM Response with Fake Names")
            
            if config.enable_performance_timing:
                start_time = time.time()
            
            fake_prompt, ner_map = fake_ner_replace(user_prompt)
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
        
        # Process XXXX masking if enabled
        if config.enable_xxxx_masking:
            st.subheader("🔵 LLM Response with XXXX Masking")
            
            if config.enable_performance_timing:
                start_time = time.time()
            
            masked_prompt, mask_map = mask_ner_with_xxxx(user_prompt)
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
        
        # Process LLM-based PII removal if enabled
        if config.enable_llm_pii_removal and 'llm_pii_remover' in imports:
            st.subheader("🟢 LLM Response with LLM-based PII Removal")
            
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
        
        # Calculate metrics only if there are responses to analyze
        if responses:
            st.markdown("---")
            st.subheader("📊 Analysis Results")

            # Semantic similarity
            similarities = calculate_semantic_similarity(responses)

            # DeepEval scores
            prompts_responses = {method: (prompts.get(method, user_prompt), response)
                               for method, response in responses.items()}
            deepeval_scores = calculate_deepeval_scores(prompts_responses)

            # PII leakage (only if real names are enabled for comparison)
            pii_scores = {}
            if config.enable_real_names and config.enable_pii_leakage_detection:
                pii_scores = calculate_pii_leakage(user_prompt, responses)

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

                if processing_times and config.show_processing_times:
                    st.markdown("**⏱️ Processing Times:**")
                    for method, time_taken in processing_times.items():
                        st.write(f"• {method.title()}: {time_taken:.3f}s")
        else:
            st.warning("⚠️ No PII protection methods are enabled. Please enable at least one method in the sidebar.")
        
        # Excel export
        if config.enable_excel_export and excel_exporter and responses:
            # Prepare comprehensive data
            analysis_data = {
                'original_prompt': user_prompt,
                **{f'{method}_prompt': prompts.get(method, user_prompt) for method in responses.keys()},
                **{f'{method}_response': response for method, response in responses.items()},
                **mappings,
                **deepeval_scores,
                **similarities,
                **pii_scores,
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
                    st.json(stats)

            with col3:
                if st.button("🗑️ Clear Data"):
                    excel_exporter.clear_data()
                    st.success("✅ Data cleared!")

if __name__ == "__main__":
    main()
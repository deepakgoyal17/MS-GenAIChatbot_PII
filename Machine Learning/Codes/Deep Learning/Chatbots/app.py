import os
import warnings
# Set offline mode for transformers to prevent network calls when models are cached
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from sentence_transformers import SentenceTransformer, util
from SimilarOrgReplacement import KnowledgeGraphReplacer #  SimilarOrgReplacement is a custom module for organization name replacement
from SimilarOrgReplacement_BetterPerformance import HybridOrganizationReplacer
from capitalizeNameAndOrg import  NameOrganizationCapitalizer # CapitalizeNameAndOrg is a custom module for name and organization capitalization
from base_logger import BaseLogger
from local_llm_pii_removal import remove_pii_with_llm
from excel_exporter import PIIAnalysisExporter
import logging

logger = BaseLogger(log_name='chatbot_app', log_level=logging.INFO, log_dir='logs').get_logger()
logger.info("Chatbot application started")

import streamlit as st

@st.cache_resource(show_spinner=False)
def get_st_model():
    """Load SentenceTransformer model with comprehensive fallback strategy"""
    models_to_try = [
        'all-MiniLM-L6-v2',
        'paraphrase-MiniLM-L6-v2',
        'all-mpnet-base-v2'
    ]
    
    for model_name in models_to_try:
        try:
            logger.info(f"Attempting to load SentenceTransformer model: {model_name}")
            # First try with offline mode disabled to allow downloads if needed
            os.environ.pop('TRANSFORMERS_OFFLINE', None)
            os.environ.pop('HF_HUB_OFFLINE', None)
            
            model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded model: {model_name}")
            
            # Re-enable offline mode after successful load
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_HUB_OFFLINE'] = '1'
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            # Try with offline mode enabled (use cached models only)
            try:
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_HUB_OFFLINE'] = '1'
                model = SentenceTransformer(model_name)
                logger.info(f"Successfully loaded cached model: {model_name}")
                return model
            except Exception as e2:
                logger.error(f"Failed to load cached {model_name}: {e2}")
                continue
    
    # If all models fail, show comprehensive error message
    st.error("⚠️ **Model Loading Issue**: Cannot load SentenceTransformer models.")
    st.info("""
    **Possible solutions:**
    1. **Check internet connection** - Models need to be downloaded on first use
    2. **Pre-download models** - Run this in terminal:
       ```python
       from sentence_transformers import SentenceTransformer
       SentenceTransformer('all-MiniLM-L6-v2')
       ```
    3. **Use VPN** - If Hugging Face is blocked in your region
    4. **Wait and retry** - Hugging Face servers might be temporarily down
    
    **Note**: Semantic similarity features will be disabled until a model is available.
    """)
    return None

# Initialize the model with error handling
st_model = get_st_model()
import os
from dotenv import load_dotenv

import google.generativeai as genai
import spacy

from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

class CustomLLM(DeepEvalBaseLLM):
    def __init__(self):
        # Initialize after API key is configured
        self.model = None
        self.model_name = "gemini-1.5-flash"

    def _ensure_model(self):
        """Ensure model is initialized with API key"""
        if self.model is None:
            try:
                # Make sure API key is configured
                if not os.getenv("GOOGLE_API_KEY"):
                    raise ValueError("GOOGLE_API_KEY not found in environment variables")
                
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.model = genai.GenerativeModel(self.model_name)
                logger.info("CustomLLM model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CustomLLM: {e}")
                raise e

    def load_model(self):
        self._ensure_model()
        return self.model

    def generate(self, prompt: str) -> str:
        self._ensure_model()
        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini model")
                return "No response generated"
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Error: {str(e)}"

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model_name

# Initialize CustomLLM after environment setup
custom_llm = None



load_dotenv()

# Check if API key is available
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ **API Key Missing**: GOOGLE_API_KEY not found in environment variables.")
    st.info("Please add your Google API key to the .env file: GOOGLE_API_KEY=your_key_here")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize CustomLLM after API configuration
custom_llm = CustomLLM()

# Initialize Excel Exporter
@st.cache_resource(show_spinner=False)
def get_excel_exporter():
    return PIIAnalysisExporter(output_dir="analysis_results", logger=logger)

excel_exporter = get_excel_exporter()

# Load spaCy English model for NER
@st.cache_resource(show_spinner=False)
def get_spacy_model():
    return spacy.load("en_core_web_sm") #  python -m spacy download en_core_web_sm
nlp = get_spacy_model()



def SmartOrgReplacement(text):
    # Initialize the replacer
    '''
    replacer = KnowledgeGraphReplacer()

# Get a single replacement

    logger.info("This is input text: %s", text)
    logger.info("This is before calling get_replacement_suggestion")
    replacement = replacer.get_replacement_suggestion(text)
    logger.info("This is after calling get_replacement_suggestion")
    print(f"Replace Microsoft with: {replacement}")  # Output: Google (or similar tech company)
    '''

    replacer = HybridOrganizationReplacer(
            enable_web_fallback=True,
            web_timeout=2.0,
            max_web_requests=10
        )
    logger.info("This is before calling replace_organizations_hybrid")
    replacement = replacer.replace_organizations_hybrid(text)[0]
    logger.info("This is after calling replace_organizations_hybrid")

    return replacement

def smart_Capitalize_UsingSpacy(text):
    capitalizer_spacy = NameOrganizationCapitalizer(method='spacy')
    capitalized_text, changes = capitalizer_spacy.capitalize_text(text)
    
    print("Capitalized text:")
    print(capitalized_text)
    print("\nChanges made:")
    for change in changes:
        print(f"  {change['original']} → {change['capitalized']} ({change['type']})")
    return capitalized_text



from faker import Faker
faker = Faker()

import re
import time

import google.generativeai as genai

# Initialize memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

 # --- Fake NER replacement setup ---
def fake_ner_replace(text):
   # Use spaCy to detect NER objects, then replace with Faker-generated values
   #text = smart_capitalize(text)  # Apply smart capitalization
   logger.info("This is input text: %s", text)
   text = smart_Capitalize_UsingSpacy(text)
   logger.info("This is Capitalized text: %s", text)
   doc = nlp(text)
   logger.info("This is NER text: %s", doc)
   logger.info("faker Object: %s", faker)
   #st.chat_message("user").markdown(doc)
   ner_map = {}
   real_to_fake = {}
   fake_text = text
   for ent in doc.ents:
       if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]:
           if ent.text not in real_to_fake:
               if ent.label_ == "PERSON":
                   real_to_fake[ent.text] = faker.name()
               elif ent.label_ == "ORG":
                   #fake_value = faker.company()
                   real_to_fake[ent.text] = SmartOrgReplacement(ent.text)  # Use the custom org replacement
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
           logger.info("This is Real text: %s", ent.text)
           logger.info("This is fake text: %s", fake_value)
           fake_text = fake_text.replace(ent.text, fake_value)

   # Additional regex-based replacements for entities not covered by spaCy
   email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
   emails = re.findall(email_pattern, fake_text)
   email_to_fake = {}
   for email in emails:
       if email not in email_to_fake:
           email_to_fake[email] = faker.email()
       fake_email = email_to_fake[email]
       if fake_email not in ner_map:
           ner_map[fake_email] = email
       logger.info("This is Real text: %s", email)
       logger.info("This is fake text: %s", fake_email)
       fake_text = fake_text.replace(email, fake_email)

   # Phone numbers
   phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
   phones = re.findall(phone_pattern, fake_text)
   phone_to_fake = {}
   for phone in phones:
       if phone not in phone_to_fake:
           phone_to_fake[phone] = faker.phone_number()
       fake_phone = phone_to_fake[phone]
       if fake_phone not in ner_map:
           ner_map[fake_phone] = phone
       logger.info("This is Real text: %s", phone)
       logger.info("This is fake text: %s", fake_phone)
       fake_text = fake_text.replace(phone, fake_phone)

   return fake_text, ner_map

def mask_ner_with_xxxx(text):
    #text = smart_capitalize(text)  # Apply smart capitalization
    text = smart_Capitalize_UsingSpacy(text)
    doc = nlp(text)
    mask_map = {}
    masked_text = text
    for ent in doc.ents:
        mask_map["XXXX"] = ent.text
        masked_text = masked_text.replace(ent.text, "XXXX")

    # Additional regex-based masking for entities not covered by spaCy
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, masked_text)
    for email in emails:
        if email not in mask_map.values():  # Avoid double masking
            masked_text = masked_text.replace(email, "XXXX")
            mask_map["XXXX"] = email

    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, masked_text)
    for phone in phones:
        if phone not in mask_map.values():  # Avoid double masking
            masked_text = masked_text.replace(phone, "XXXX")
            mask_map["XXXX"] = phone

    return masked_text, mask_map

def restore_fake_ner(text, ner_map):
    for fake_value, real_value in ner_map.items():
        text = text.replace(fake_value, real_value)
    return text
# Input box
user_prompt = st.chat_input("Ask me anything...")

if user_prompt:
    # 1. Real input (no masking)
    st.subheader("LLM Response with Real Names")
    st.chat_message("user").markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    gemini_compatible_history_real = [
        {
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        }
        for msg in st.session_state.chat_history
    ]
    start = time.time()
    response_real = model.generate_content(gemini_compatible_history_real)
    real_time = time.time() - start
    st.chat_message("assistant").markdown(response_real.text)
    st.session_state.chat_history.append({"role": "assistant", "content": response_real.text})

    # DeepEval - with LLMTestCase (FIXED)
    try:
        logger.info("Starting DeepEval relevancy measurement for real response")
        
        # Create LLMTestCase object as required by DeepEval
        test_case_real = LLMTestCase(
            input=user_prompt,
            actual_output=response_real.text
        )
        
        relevancy_real = AnswerRelevancyMetric(model=custom_llm)
        
        # Add debug information
        logger.info(f"Question: {user_prompt[:100]}...")
        logger.info(f"Answer: {response_real.text[:100]}...")
        
        # Use evaluate method with LLMTestCase
        relevancy_real.measure(test_case_real)
        relevancy_real_score = relevancy_real.score
        
        logger.info(f"DeepEval relevancy score for real response: {relevancy_real_score}")
        
        # If score is 0, check if there's additional information
        if relevancy_real_score == 0.0:
            logger.warning("DeepEval returned score of 0.0 - this might indicate an issue")
            if hasattr(relevancy_real, 'reason'):
                logger.info(f"DeepEval reason: {relevancy_real.reason}")
        
    except Exception as e:
        logger.error(f"DeepEval relevancy measurement failed for real response: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        relevancy_real_score = 0.0
        
        # Show error in UI for debugging
        st.warning(f"⚠️ DeepEval Error (Real): {str(e)}")

    # 2. Fake names
    st.subheader("LLM Response with Fake Names")
    start = time.time()
    fake_prompt, ner_map = fake_ner_replace(user_prompt)
    st.session_state.ner_map = ner_map
    st.chat_message("user").markdown(fake_prompt)
    st.session_state.chat_history.append({"role": "user", "content": fake_prompt})
    if ner_map:
        st.info(f"**Fake NER mapping:** {ner_map}")
    gemini_compatible_history_fake = [
        {
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        }
        for msg in st.session_state.chat_history
    ]
    response_fake = model.generate_content(gemini_compatible_history_fake)
    bot_reply_fake = restore_fake_ner(response_fake.text, st.session_state.ner_map)
    fake_time = time.time() - start
    st.chat_message("assistant").markdown(bot_reply_fake)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply_fake})

    # DeepEval - with LLMTestCase (FIXED)
    try:
        logger.info("Starting DeepEval relevancy measurement for fake response")
        
        # Create LLMTestCase object
        test_case_fake = LLMTestCase(
            input=fake_prompt,
            actual_output=bot_reply_fake
        )
        
        relevancy_fake = AnswerRelevancyMetric(model=custom_llm)
        relevancy_fake.measure(test_case_fake)
        relevancy_fake_score = relevancy_fake.score
        logger.info(f"DeepEval relevancy score for fake response: {relevancy_fake_score}")
    except Exception as e:
        logger.error(f"DeepEval relevancy measurement failed for fake response: {e}")
        relevancy_fake_score = 0.0
        st.warning(f"⚠️ DeepEval Error (Fake): {str(e)}")

    # 3. Masked with XXXX
    st.subheader("LLM Response with XXXX Masking")
    start = time.time()
    masked_prompt, mask_map = mask_ner_with_xxxx(user_prompt)
    st.session_state.mask_map = mask_map
    st.chat_message("user").markdown(masked_prompt)
    st.session_state.chat_history.append({"role": "user", "content": masked_prompt})
    if mask_map:
        st.info(f"**XXXX Mask mapping:** {mask_map}")
    gemini_compatible_history_mask = [
        {
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        }
        for msg in st.session_state.chat_history
    ]
    response_mask = model.generate_content(gemini_compatible_history_mask)
    bot_reply_mask = response_mask.text.replace("XXXX", ", ".join(mask_map.values()))
    mask_time = time.time() - start
    st.chat_message("assistant").markdown(bot_reply_mask)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply_mask})

    # DeepEval - with LLMTestCase (FIXED)
    try:
        logger.info("Starting DeepEval relevancy measurement for masked response")
        
        # Create LLMTestCase object
        test_case_mask = LLMTestCase(
            input=masked_prompt,
            actual_output=bot_reply_mask
        )
        
        relevancy_mask = AnswerRelevancyMetric(model=custom_llm)
        relevancy_mask.measure(test_case_mask)
        relevancy_mask_score = relevancy_mask.score
        logger.info(f"DeepEval relevancy score for masked response: {relevancy_mask_score}")
    except Exception as e:
        logger.error(f"DeepEval relevancy measurement failed for masked response: {e}")
        relevancy_mask_score = 0.0
        st.warning(f"⚠️ DeepEval Error (Masked): {str(e)}")

    # 4. LLM-based PII removal
    st.subheader("LLM Response with LLM-based PII Removal")
    start = time.time()
    llm_anonymized_prompt = remove_pii_with_llm(user_prompt)
    st.chat_message("user").markdown(llm_anonymized_prompt)
    st.session_state.chat_history.append({"role": "user", "content": llm_anonymized_prompt})
    gemini_compatible_history_llm = [
        {
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        }
        for msg in st.session_state.chat_history
    ]
    response_llm = model.generate_content(gemini_compatible_history_llm)
    llm_time = time.time() - start
    st.chat_message("assistant").markdown(response_llm.text)
    st.session_state.chat_history.append({"role": "assistant", "content": response_llm.text})

    # DeepEval - with LLMTestCase (FIXED)
    try:
        logger.info("Starting DeepEval relevancy measurement for LLM response")
        
        # Create LLMTestCase object
        test_case_llm = LLMTestCase(
            input=llm_anonymized_prompt,
            actual_output=response_llm.text
        )
        
        relevancy_llm = AnswerRelevancyMetric(model=custom_llm)
        relevancy_llm.measure(test_case_llm)
        relevancy_llm_score = relevancy_llm.score
        logger.info(f"DeepEval relevancy score for LLM response: {relevancy_llm_score}")
    except Exception as e:
        logger.error(f"DeepEval relevancy measurement failed for LLM response: {e}")
        relevancy_llm_score = 0.0
        st.warning(f"⚠️ DeepEval Error (LLM): {str(e)}")

    # --- Metrics ---
    # For demo: compare if LLM response contains any of the real names (or fake names)
    doc = nlp(user_prompt)
    real_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    fake_names = list(ner_map.keys())
    mask_names = list(mask_map.values())
    real_score = sum(name in response_real.text for name in real_names)
    fake_score = sum(fake in response_fake.text for fake in real_names)
    mask_score = sum(mask in response_mask.text for mask in real_names)
    llm_score = sum(name in response_llm.text for name in real_names)
    # F1 score: 1 if no real PII leaked, else 0 (simplified)
    real_f1 = 1 if real_score == 0 else 0
    fake_f1 = 1 if fake_score == 0 else 0
    mask_f1 = 1 if mask_score == 0 else 0
    llm_f1 = 1 if llm_score == 0 else 0
    st.markdown(f"**Metrics:**<br>Real name match: {real_score}, Fake name match: {fake_score}, Masked name match: {mask_score}, LLM name match: {llm_score}<br>**F1 Score (PII Leakage):**<br>Real: {real_f1}, Fake: {fake_f1}, Masked: {mask_f1}, LLM: {llm_f1}", unsafe_allow_html=True)

    # --- Semantic Similarity ---
    if st_model is not None:
        try:
            real_resp = response_real.text
            fake_resp = bot_reply_fake
            mask_resp = bot_reply_mask
            llm_resp = response_llm.text
            emb_real = st_model.encode(real_resp, convert_to_tensor=True)
            emb_fake = st_model.encode(fake_resp, convert_to_tensor=True)
            emb_mask = st_model.encode(mask_resp, convert_to_tensor=True)
            emb_llm = st_model.encode(llm_resp, convert_to_tensor=True)
            sim_real_fake = float(util.cos_sim(emb_real, emb_fake))
            sim_real_mask = float(util.cos_sim(emb_real, emb_mask))
            sim_fake_mask = float(util.cos_sim(emb_fake, emb_mask))
            sim_real_llm = float(util.cos_sim(emb_real, emb_llm))
            sim_fake_llm = float(util.cos_sim(emb_fake, emb_llm))
            sim_mask_llm = float(util.cos_sim(emb_mask, emb_llm))
            st.markdown(f"**Semantic Similarity:**<br>Real vs Fake: {sim_real_fake:.3f}<br>Real vs Masked: {sim_real_mask:.3f}<br>Fake vs Masked: {sim_fake_mask:.3f}<br>Real vs LLM: {sim_real_llm:.3f}<br>Fake vs LLM: {sim_fake_llm:.3f}<br>Masked vs LLM: {sim_mask_llm:.3f}", unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            st.warning("⚠️ Semantic similarity calculation unavailable due to model loading issues.")
    else:
        st.warning("⚠️ Semantic similarity features disabled - SentenceTransformer model not available.")

    st.markdown(f"**Time Taken:**<br>Real: {real_time:.3f}s<br>Fake: {fake_time:.3f}s<br>Masked: {mask_time:.3f}s<br>LLM: {llm_time:.3f}s", unsafe_allow_html=True)

    st.markdown(f"**DeepEval Answer Relevancy:**<br>Real: {relevancy_real_score:.3f}<br>Fake: {relevancy_fake_score:.3f}<br>Masked: {relevancy_mask_score:.3f}<br>LLM: {relevancy_llm_score:.3f}", unsafe_allow_html=True)

    # --- Excel Export ---
    # Prepare data for Excel export
    analysis_data = {
        'original_prompt': user_prompt,
        'real_response': response_real.text,
        'fake_prompt': fake_prompt,
        'fake_response': bot_reply_fake,
        'masked_prompt': masked_prompt,
        'masked_response': bot_reply_mask,
        'llm_anonymized_prompt': llm_anonymized_prompt,
        'llm_response': response_llm.text,
        'ner_mapping': ner_map,
        'mask_mapping': mask_map,
        
        # Relevancy scores
        'relevancy_real': relevancy_real_score,
        'relevancy_fake': relevancy_fake_score,
        'relevancy_masked': relevancy_mask_score,
        'relevancy_llm': relevancy_llm_score,
        
        # Semantic similarity scores
        'similarity_real_fake': sim_real_fake if st_model else 0.0,
        'similarity_real_masked': sim_real_mask if st_model else 0.0,
        'similarity_real_llm': sim_real_llm if st_model else 0.0,
        'similarity_fake_masked': sim_fake_mask if st_model else 0.0,
        'similarity_fake_llm': sim_fake_llm if st_model else 0.0,
        'similarity_mask_llm': sim_mask_llm if st_model else 0.0,
        
        # Processing times
        'processing_time_real': real_time,
        'processing_time_fake': fake_time,
        'processing_time_masked': mask_time,
        'processing_time_llm': llm_time,
        
        # PII leakage scores
        'pii_leakage_real': real_score,
        'pii_leakage_fake': fake_score,
        'pii_leakage_masked': mask_score,
        'pii_leakage_llm': llm_score,
        
        # F1 scores
        'f1_real': real_f1,
        'f1_fake': fake_f1,
        'f1_masked': mask_f1,
        'f1_llm': llm_f1,
        
        # Additional metrics
        'entities_detected': len([ent for ent in nlp(user_prompt).ents if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]])
    }
    
    # Add to Excel exporter
    excel_exporter.add_analysis_record(analysis_data)
    
    # Show export options
    st.markdown("---")
    st.subheader("📊 Data Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export to Excel", help="Export all analysis data to Excel file"):
            try:
                filepath = excel_exporter.export_to_excel()
                if filepath:
                    st.success(f"✅ Data exported successfully!")
                    st.info(f"📁 File saved: `{filepath}`")
                    
                    # Show current stats
                    stats = excel_exporter.get_current_stats()
                    st.write(f"**Total queries processed:** {stats['total_queries']}")
                else:
                    st.error("❌ Export failed. Check logs for details.")
            except Exception as e:
                st.error(f"❌ Export error: {str(e)}")
                logger.error(f"Excel export failed: {e}")
    
    with col2:
        if st.button("📈 Show Current Stats", help="Display current session statistics"):
            stats = excel_exporter.get_current_stats()
            st.json(stats)
    
    with col3:
        if st.button("🗑️ Clear Data", help="Clear all stored analysis data"):
            excel_exporter.clear_data()
            st.success("✅ All analysis data cleared!")


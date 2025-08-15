from sentence_transformers import SentenceTransformer, util
from SimilarOrgReplacement import KnowledgeGraphReplacer #  SimilarOrgReplacement is a custom module for organization name replacement
from SimilarOrgReplacement_BetterPerformance import HybridOrganizationReplacer
from capitalizeNameAndOrg import  NameOrganizationCapitalizer # CapitalizeNameAndOrg is a custom module for name and organization capitalization
from base_logger import BaseLogger
import logging

logger = BaseLogger(log_name='chatbot_app', log_level=logging.INFO, log_dir='logs').get_logger()
logger.info("Chatbot application started")

import streamlit as st
@st.cache_resource(show_spinner=False)
def get_st_model():
    return SentenceTransformer('all-MiniLM-L6-v2')
st_model = get_st_model()
import os
from dotenv import load_dotenv

import google.generativeai as genai
import spacy



load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE-API-KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

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
    replacement = replacer.replace_organizations_hybrid(st.text)[0]
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
    fake_text = text
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            fake_value = faker.name()
        elif ent.label_ == "ORG":
            #fake_value = faker.company()
             fake_value = SmartOrgReplacement(ent.text)  # Use the custom org replacement
        elif ent.label_ == "GPE":
            fake_value = faker.city()
        elif ent.label_ == "DATE":
            fake_value = faker.date()
        elif ent.label_ == "EMAIL":
            fake_value = faker.email()
        elif ent.label_ == "PHONE":
            fake_value = faker.phone_number()
     #   else:
       #     fake_value = faker.word()
        ner_map[fake_value] = ent.text
        logger.info("This is Real text: %s", ent.text)
        logger.info("This is fake text: %s", fake_value)
        fake_text = fake_text.replace(ent.text, fake_value)
        
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
    response_real = model.generate_content(gemini_compatible_history_real)
    st.chat_message("assistant").markdown(response_real.text)
    st.session_state.chat_history.append({"role": "assistant", "content": response_real.text})

    # 2. Fake names
    st.subheader("LLM Response with Fake Names")
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
    st.chat_message("assistant").markdown(bot_reply_fake)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply_fake})

    # 3. Masked with XXXX
    st.subheader("LLM Response with XXXX Masking")
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
    st.chat_message("assistant").markdown(bot_reply_mask)
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply_mask})

    # --- Metrics ---
    # For demo: compare if LLM response contains any of the real names (or fake names)
    doc = nlp(user_prompt)
    real_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    fake_names = list(ner_map.keys())
    mask_names = list(mask_map.values())
    real_score = sum(name in response_real.text for name in real_names)
    fake_score = sum(fake in response_fake.text for fake in fake_names)
    mask_score = sum(mask in response_mask.text for mask in mask_names)
    st.markdown(f"**Metrics:**<br>Real name match: {real_score}, Fake name match: {fake_score}, Masked name match: {mask_score}", unsafe_allow_html=True)

    # --- Semantic Similarity ---
    real_resp = response_real.text
    fake_resp = bot_reply_fake
    mask_resp = bot_reply_mask
    emb_real = st_model.encode(real_resp, convert_to_tensor=True)
    emb_fake = st_model.encode(fake_resp, convert_to_tensor=True)
    emb_mask = st_model.encode(mask_resp, convert_to_tensor=True)
    sim_real_fake = float(util.cos_sim(emb_real, emb_fake))
    sim_real_mask = float(util.cos_sim(emb_real, emb_mask))
    sim_fake_mask = float(util.cos_sim(emb_fake, emb_mask))
    st.markdown(f"**Semantic Similarity:**<br>Real vs Fake: {sim_real_fake:.3f}<br>Real vs Masked: {sim_real_mask:.3f}<br>Fake vs Masked: {sim_fake_mask:.3f}", unsafe_allow_html=True)


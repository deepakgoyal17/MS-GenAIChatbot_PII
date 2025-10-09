# 📋 App.py Code Explanation

## 🎯 Overview

This Streamlit application is a **PII (Personally Identifiable Information) Protection Research Chatbot** that demonstrates different approaches to handling sensitive data in conversational AI. It processes user input through 4 different PII protection methods and compares their effectiveness.

## 🏗️ Architecture Components

### 1. **Initialization & Setup** (Lines 1-120)

#### Environment Configuration
```python
# Set offline mode for transformers
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
```
- Configures offline mode to prevent unnecessary network calls
- Suppresses warnings for cleaner output

#### Model Loading with Fallback Strategy
```python
@st.cache_resource(show_spinner=False)
def get_st_model():
    models_to_try = ['all-MiniLM-L6-v2', 'paraphrase-MiniLM-L6-v2', 'all-mpnet-base-v2']
```
- **Purpose**: Load SentenceTransformer models for semantic similarity calculations
- **Fallback Strategy**: Tries multiple models if primary fails
- **Caching**: Uses Streamlit's `@st.cache_resource` for performance

#### Core Components Initialization
- **Logger**: Custom logging system for debugging and monitoring
- **Gemini AI**: Google's Generative AI model for chat responses
- **spaCy NLP**: For Named Entity Recognition (NER)
- **DeepEval**: For answer relevancy evaluation

### 2. **Custom Classes** (Lines 90-107)

#### CustomLLM Class
```python
class CustomLLM(DeepEvalBaseLLM):
    def __init__(self):
        self.model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text
```
- **Purpose**: Wrapper for Gemini AI to work with DeepEval metrics
- **Inheritance**: Extends `DeepEvalBaseLLM` for compatibility
- **Methods**: Implements required methods for evaluation

### 3. **PII Processing Functions** (Lines 123-269)

#### A. Smart Organization Replacement
```python
def SmartOrgReplacement(text):
    replacer = HybridOrganizationReplacer(
        enable_web_fallback=True,
        web_timeout=2.0,
        max_web_requests=10
    )
    replacement = replacer.replace_organizations_hybrid(text)[0]
    return replacement
```
- **Purpose**: Replace organization names with similar ones
- **Method**: Uses hybrid approach with web fallback
- **Example**: "Microsoft" → "Google" (similar tech company)

#### B. Smart Capitalization
```python
def smart_Capitalize_UsingSpacy(text):
    capitalizer_spacy = NameOrganizationCapitalizer(method='spacy')
    capitalized_text, changes = capitalizer_spacy.capitalize_text(text)
    return capitalized_text
```
- **Purpose**: Proper capitalization of names and organizations
- **Method**: Uses spaCy NER for intelligent capitalization

#### C. Fake NER Replacement
```python
def fake_ner_replace(text):
    # Process through spaCy NER
    doc = nlp(text)
    real_to_fake = {}
    
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EMAIL", "PHONE"]:
            if ent.label_ == "PERSON":
                real_to_fake[ent.text] = faker.name()
            elif ent.label_ == "ORG":
                real_to_fake[ent.text] = SmartOrgReplacement(ent.text)
            # ... other entity types
```
- **Purpose**: Replace real PII with fake but realistic data
- **Entities Handled**: Person names, organizations, locations, dates, emails, phones
- **Mapping**: Maintains bidirectional mapping for restoration

#### D. XXXX Masking
```python
def mask_ner_with_xxxx(text):
    doc = nlp(text)
    masked_text = text
    for ent in doc.ents:
        masked_text = masked_text.replace(ent.text, "XXXX")
```
- **Purpose**: Replace all PII with generic "XXXX" placeholder
- **Method**: Simple masking approach

### 4. **Main Application Flow** (Lines 271-433)

When a user submits input, the application processes it through **4 parallel pipelines**:

#### Pipeline 1: Real Names (No Protection)
```python
st.subheader("LLM Response with Real Names")
response_real = model.generate_content(gemini_compatible_history_real)
```
- **Purpose**: Baseline - no PII protection
- **Use Case**: Shows what happens without protection

#### Pipeline 2: Fake Names
```python
st.subheader("LLM Response with Fake Names")
fake_prompt, ner_map = fake_ner_replace(user_prompt)
response_fake = model.generate_content(gemini_compatible_history_fake)
bot_reply_fake = restore_fake_ner(response_fake.text, ner_map)
```
- **Process**: Input → Fake NER → LLM → Restore Real Names → Output
- **Advantage**: Maintains context while protecting PII

#### Pipeline 3: XXXX Masking
```python
st.subheader("LLM Response with XXXX Masking")
masked_prompt, mask_map = mask_ner_with_xxxx(user_prompt)
response_mask = model.generate_content(gemini_compatible_history_mask)
```
- **Process**: Input → Mask with XXXX → LLM → Replace XXXX → Output
- **Trade-off**: High privacy but may lose context

#### Pipeline 4: LLM-based PII Removal
```python
st.subheader("LLM Response with LLM-based PII Removal")
llm_anonymized_prompt = remove_pii_with_llm(user_prompt)
response_llm = model.generate_content(gemini_compatible_history_llm)
```
- **Process**: Input → LLM Anonymization → LLM Response
- **Method**: Uses another LLM to intelligently remove PII

### 5. **Evaluation & Metrics** (Lines 389-433)

#### A. PII Leakage Detection
```python
real_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
real_score = sum(name in response_real.text for name in real_names)
real_f1 = 1 if real_score == 0 else 0  # Binary: leaked or not
```
- **Purpose**: Check if original PII appears in responses
- **Metric**: Binary F1 score (1 = no leakage, 0 = leakage detected)

#### B. Semantic Similarity Analysis
```python
emb_real = st_model.encode(real_resp, convert_to_tensor=True)
emb_fake = st_model.encode(fake_resp, convert_to_tensor=True)
sim_real_fake = float(util.cos_sim(emb_real, emb_fake))
```
- **Purpose**: Measure how similar responses are semantically
- **Method**: Cosine similarity between sentence embeddings
- **Comparison**: All methods compared against baseline (real names)

#### C. Answer Relevancy (DeepEval)
```python
relevancy_real = AnswerRelevancyMetric(model=custom_llm)
relevancy_real.measure(user_prompt, response_real.text)
```
- **Purpose**: Evaluate how relevant responses are to original questions
- **Tool**: DeepEval framework for LLM evaluation
- **Metric**: Relevancy score (0-1)

#### D. Performance Timing
```python
start = time.time()
# ... processing ...
real_time = time.time() - start
```
- **Purpose**: Measure processing time for each method
- **Use Case**: Compare computational overhead

## 🔄 Data Flow Summary

```
User Input
    ↓
┌─────────────────────────────────────────────────────────────┐
│                    4 Parallel Pipelines                     │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Real      │    Fake     │    XXXX     │   LLM-based     │
│   Names     │    Names    │   Masking   │   Removal       │
│     ↓       │      ↓      │      ↓      │        ↓        │
│   No PII    │  Fake PII   │  Mask PII   │  Remove PII     │
│ Protection  │ Replacement │  with XXXX  │  Intelligently  │
│     ↓       │      ↓      │      ↓      │        ↓        │
│  Gemini AI  │  Gemini AI  │  Gemini AI  │   Gemini AI     │
│     ↓       │      ↓      │      ↓      │        ↓        │
│  Response   │  Restore    │  Replace    │   Response      │
│             │  Real Names │  XXXX       │                 │
└─────────────┴─────────────┴─────────────┴─────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│                    Evaluation Metrics                       │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ PII Leakage │  Semantic   │   Answer    │   Processing    │
│  Detection  │ Similarity  │ Relevancy   │     Time        │
│   (F1)      │ (Cosine)    │ (DeepEval)  │  (Seconds)      │
└─────────────┴─────────────┴─────────────┴─────────────────┘
    ↓
  Results Display
```

## 🎯 Key Features

1. **Multi-Method Comparison**: Tests 4 different PII protection approaches
2. **Comprehensive Evaluation**: Multiple metrics for thorough analysis
3. **Error Resilience**: Graceful handling of model loading failures
4. **Real-time Processing**: Interactive Streamlit interface
5. **Detailed Logging**: Comprehensive logging for debugging
6. **Fallback Mechanisms**: Multiple backup strategies for reliability

## 🔍 Research Purpose

This application is designed for **PII protection research** in conversational AI, allowing researchers to:

- Compare effectiveness of different anonymization methods
- Measure trade-offs between privacy and utility
- Evaluate semantic preservation across methods
- Analyze computational overhead of each approach
- Study PII leakage patterns in LLM responses

The multi-pipeline approach provides comprehensive insights into how different PII protection methods affect both privacy and conversational quality.
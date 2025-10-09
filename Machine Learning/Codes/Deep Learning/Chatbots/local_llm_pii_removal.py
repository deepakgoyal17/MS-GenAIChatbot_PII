from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Ollama LLM
llm = OllamaLLM(model="llama3.1", temperature=0.1, base_url="http://localhost:11434")

def remove_pii_with_llm(text):
    """
    Use local LLM to remove PII from text by replacing sensitive information with placeholders.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", ''' You are a data anonymization assistant. Replace PII as follows:
- Names: Use fake names like "John Smith", "Jane Doe", "Mike Wilson" 
- Emails: Use fake emails like "john.smith@example.com"
- Phone: Use format "555-0123"
- Addresses: Use "123 Main St, Anytown, ST 12345"

Maintain consistent fake identities throughout the text (same person gets same fake name) '''),
        ("user", "Anonymize this text: {text}")
    ])

    chain = prompt | llm | StrOutputParser()
    anonymized_text = chain.invoke({'text': text})
    return anonymized_text.strip()

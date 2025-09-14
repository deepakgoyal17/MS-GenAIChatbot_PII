from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms.ollama import Ollama
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Ollama LLM
llm = Ollama(model="llama3.1", temperature=0.1)

def remove_pii_with_llm(text):
    """
    Use local LLM to remove PII from text by replacing sensitive information with placeholders.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a data anonymization assistant. Your role is to protect privacy by replacing personally identifiable information (PII) in text with placeholders. Replace names with [NAME], emails with [EMAIL], phone numbers with [PHONE], addresses with [ADDRESS], dates with [DATE], etc. Maintain the original text structure and meaning. This is for legitimate data protection purposes. Always perform the anonymization and output only the modified text."),
        ("user", "Anonymize this text: {text}")
    ])

    chain = prompt | llm | StrOutputParser()
    anonymized_text = chain.invoke({'text': text})
    return anonymized_text.strip()
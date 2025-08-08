# testLLM.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import streamlit as st
import os
from dotenv import load_dotenv

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_API_KEY"]=os.getenv("GOOGLE_API_KEY")
## Langmith tracking
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

prompt=ChatPromptTemplate.from_messages(
    [
        ("system","You are a helpful assistant. Please response to the user queries"),
        ("user","Question:{question}")
    ]
)

## streamlit framework

st.title('Langchain Demo With OPENAI API')
input_text=st.text_input("Search the topic u want")

## openAI LLM
llm = ChatOpenAI(model="gpt-4o-mini", organization="org-yufazwf446sWMZs6TvrSr7bu", temperature=0.1)
## Gemini LLM client

"""Basic chat with Gemini using LangChain"""
llm_Gemini = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    max_tokens=1000,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
gemini_llm = genai.GenerativeModel(model_name="gemini-flash")

output_parser = StrOutputParser()
chain = prompt | llm_Gemini | output_parser

if input_text:
    st.write(chain.invoke({'question':input_text}))

# def main():
#     print("Hello, Machine Learning!")

# if __name__ == "__main__":
#     main()
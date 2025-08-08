# Standard library imports
import os
from typing import Dict, List, Any
from datetime import datetime
import json

# LangChain imports for building the chatbot
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI  # ChatGPT-style models
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory  # Memory management
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage  # Message types
from langchain.chains import ConversationChain  # Chain for conversation flow
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder  # Prompt engineering
from langchain.callbacks.base import BaseCallbackHandler  # For custom callbacks
from langchain.schema.runnable import RunnablePassthrough  # For chain composition
from langchain.schema.output_parser import StrOutputParser  # Parse LLM output to string

class BankingChatbot:
    """
    Commercial Banking Chatbot with context memory using LangChain
    Handles customer inquiries about banking services, account management, and financial products
    """
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the banking chatbot
        
        Args:
            openai_api_key: OpenAI API key for accessing GPT models
            model_name: Which OpenAI model to use (gpt-3.5-turbo, gpt-4, etc.)
        """
        # Initialize the ChatGPT model with specific parameters
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=0.3  # Lower temperature (0-1) = more consistent/focused responses
                            # Higher temperature = more creative/random responses
        )
        
        # ConversationBufferWindowMemory keeps the last 'k' exchanges in memory
        # This prevents the context from growing infinitely while maintaining recent context
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 human-AI message pairs
            return_messages=True,  # Return as Message objects instead of strings
            memory_key="chat_history"  # Key name for accessing memory in prompts
        )
        
        # Dictionary to store customer-specific information across conversations
        # In production, this would likely be a database
        self.customer_context = {}
        
        # Set up the conversation chain (connects prompt -> LLM -> output parser)
        self.setup_conversation_chain()
    
    def setup_conversation_chain(self):
        """
        Setup the conversation chain with banking-specific prompts
        
        A chain in LangChain connects: Prompt Template -> LLM -> Output Parser
        This creates a reusable pipeline for processing conversations
        """
        
        # This is the "system prompt" that defines the AI's role and behavior
        # It's sent with every conversation to maintain consistent behavior
        system_prompt = """You are a professional commercial banking assistant helping business customers. 
        You specialize in:
        - Business account management
        - Commercial loans and credit facilities
        - Cash management services
        - Trade finance and letters of credit
        - Investment services for businesses
        - Treasury management
        
        Guidelines:
        1. Always maintain a professional, helpful tone
        2. Provide accurate information about banking services
        3. If you don't know specific account details, ask the customer to verify with their relationship manager
        4. For sensitive operations, remind customers to use secure banking channels
        5. Escalate complex issues to human agents when necessary
        6. Remember context from previous messages in the conversation
        
        Current conversation context: {chat_history}
        Customer query: {input}
        
        Response:"""
        
        # ChatPromptTemplate structures how messages are sent to the LLM
        # It combines system instructions, conversation history, and current input
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),  # Always sent first - defines AI behavior
            MessagesPlaceholder(variable_name="chat_history"),  # Inserts conversation history here
            ("human", "{input}")  # Current user message
        ])
        
        # Create the chain: Prompt -> LLM -> String Parser
        # The | operator connects these components in sequence
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def set_customer_context(self, customer_id: str, context: Dict[str, Any]):
        """
        Set customer-specific context information
        
        This allows the chatbot to remember customer details across conversations
        In a real banking system, this would integrate with customer databases
        
        Args:
            customer_id: Unique customer identifier (account number, etc.)
            context: Dictionary containing customer information (name, account type, etc.)
        """
        self.customer_context[customer_id] = {
            **context,  # Spread operator - includes all items from context dict
            "last_interaction": datetime.now().isoformat()  # Track when we last talked to this customer
        }
    
    def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve customer context if available
        Returns empty dict if customer not found
        """
        return self.customer_context.get(customer_id, {})
    
    def chat(self, message: str, customer_id: str = None) -> str:
        """
        Process a customer message and return response
        
        This is the main method that handles the conversation flow:
        1. Enhances message with customer context if available
        2. Retrieves conversation history from memory
        3. Processes through the LLM chain
        4. Saves the exchange to memory
        5. Updates customer interaction timestamp
        
        Args:
            message: Customer's message
            customer_id: Optional customer identifier for personalized context
            
        Returns:
            Chatbot response string
        """
        try:
            # Enhance the message with customer context if we have it
            enhanced_message = message
            if customer_id and customer_id in self.customer_context:
                context = self.customer_context[customer_id]
                # Prepend customer context to help the AI provide personalized responses
                context_info = f"Customer Context: {json.dumps(context, indent=2)}\n\nCustomer Message: {message}"
                enhanced_message = context_info
            
            # Get the conversation history from memory
            # This will be inserted into the prompt template
            chat_history = self.memory.chat_memory.messages
            
            # Run the message through our chain: prompt -> LLM -> string output
            response = self.chain.invoke({
                "input": enhanced_message,  # Current message (possibly with context)
                "chat_history": chat_history  # Previous conversation
            })
            
            # Save this exchange to memory for future context
            # This updates the conversation history for next time
            self.memory.save_context(
                {"input": message},  # Save original message (not enhanced version)
                {"output": response}  # Save AI response
            )
            
            # Update customer's last interaction timestamp
            if customer_id:
                if customer_id not in self.customer_context:
                    self.customer_context[customer_id] = {}
                self.customer_context[customer_id]["last_interaction"] = datetime.now().isoformat()
            
            return response
            
        except Exception as e:
            # Graceful error handling - always provide a helpful response
            return f"I apologize, but I'm experiencing technical difficulties. Please contact your relationship manager for immediate assistance. Error: {str(e)}"
    
    def clear_memory(self):
        """
        Clear conversation memory
        Useful when starting a fresh conversation or switching customers
        """
        self.memory.clear()
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """
        Get the current conversation history as a list of Message objects
        Useful for debugging or creating conversation summaries
        """
        return self.memory.chat_memory.messages
    
    def save_conversation_summary(self, customer_id: str) -> str:
        """
        Generate and save a summary of the conversation
        
        This is useful for:
        - Record keeping and compliance
        - Handoffs to human agents
        - Customer service follow-up
        - Training data for improving the chatbot
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Generated conversation summary
        """
        messages = self.get_conversation_history()
        if not messages:
            return "No conversation to summarize."
        
        # Create a prompt specifically for summarization
        summary_prompt = """Please provide a concise summary of this banking customer conversation, 
        highlighting key topics discussed, any issues raised, and any follow-up actions needed:
        
        Conversation:
        """
        
        # Convert message objects to readable text format
        conversation_text = "\n".join([
            f"{'Customer' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in messages
        ])
        
        # Use the LLM to generate a summary
        summary_response = self.llm.invoke([
            SystemMessage(content=summary_prompt + conversation_text)
        ])
        
        # Store the summary in customer context for future reference
        if customer_id not in self.customer_context:
            self.customer_context[customer_id] = {}
        
        self.customer_context[customer_id]["last_conversation_summary"] = summary_response.content
        self.customer_context[customer_id]["summary_date"] = datetime.now().isoformat()
        
        return summary_response.content

# Enhanced Banking Chatbot with Advanced Memory Management
class AdvancedBankingChatbot(BankingChatbot):
    """
    Advanced version with summary memory and session management
    
    Key improvements over basic version:
    1. ConversationSummaryBufferMemory - automatically summarizes old conversations
       to save memory while retaining important context
    2. Session management - tracks individual customer sessions with metadata
    3. Better scalability for longer conversations
    """
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-3.5-turbo"):
        # Initialize the parent class first
        super().__init__(openai_api_key, model_name)
        
        # ConversationSummaryBufferMemory automatically creates summaries when
        # conversation gets too long, keeping recent messages + summary of old ones
        self.summary_memory = ConversationSummaryBufferMemory(
            llm=self.llm,  # Uses same LLM to create summaries
            max_token_limit=1000,  # When to start summarizing (approximate token count)
            return_messages=True,  # Return as Message objects
            memory_key="chat_history"
        )
        
        # Dictionary to track active customer sessions
        # In production, this would be stored in a database
        self.active_sessions = {}
    
    def start_session(self, customer_id: str, customer_info: Dict[str, Any] = None):
        """
        Start a new customer session
        
        Sessions help track individual customer interactions and provide
        better analytics and session management capabilities
        
        Args:
            customer_id: Unique customer identifier
            customer_info: Optional dictionary of customer information
            
        Returns:
            session_id: Unique identifier for this session
        """
        # Create unique session ID with timestamp
        session_id = f"{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store session metadata
        self.active_sessions[customer_id] = {
            "session_id": session_id,
            "start_time": datetime.now(),
            "customer_info": customer_info or {},
            "message_count": 0  # Track how many messages in this session
        }
        
        # Clear any previous conversation memory for a fresh start
        # Each session should start clean
        self.summary_memory.clear()
        
        return session_id
    
    def chat_with_session(self, message: str, customer_id: str) -> str:
        """
        Enhanced chat method with session management
        
        This method:
        1. Automatically starts a session if none exists
        2. Uses summary memory instead of regular memory (better for long conversations)
        3. Tracks message count per session
        4. Maintains all the context benefits of the basic chat method
        
        Args:
            message: Customer's message
            customer_id: Customer identifier
            
        Returns:
            Chatbot response
        """
        # Auto-start session if customer doesn't have an active one
        if customer_id not in self.active_sessions:
            self.start_session(customer_id)
        
        # Track engagement metrics
        self.active_sessions[customer_id]["message_count"] += 1
        
        # Get conversation history from summary memory
        # This may include actual recent messages + summaries of older messages
        chat_history = self.summary_memory.chat_memory.messages
        
        # Process message through the same chain as basic version
        response = self.chain.invoke({
            "input": message,
            "chat_history": chat_history
        })
        
        # Save to summary memory instead of regular memory
        # This automatically handles summarization when needed
        self.summary_memory.save_context(
            {"input": message}, 
            {"output": response}
        )
        
        return response
    
    def end_session(self, customer_id: str) -> Dict[str, Any]:
        """
        End customer session and return comprehensive summary
        
        This method:
        1. Calculates session duration and metrics
        2. Generates a conversation summary
        3. Cleans up session data
        4. Returns detailed session analytics
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Dictionary containing session summary and analytics
        """
        if customer_id not in self.active_sessions:
            return {"error": "No active session found"}
        
        # Get session information before cleaning up
        session_info = self.active_sessions[customer_id]
        
        # Generate conversation summary using parent class method
        summary = self.save_conversation_summary(customer_id)
        
        # Create comprehensive session summary with analytics
        session_summary = {
            "session_id": session_info["session_id"],
            "duration": str(datetime.now() - session_info["start_time"]),  # How long the session lasted
            "message_count": session_info["message_count"],  # Number of exchanges
            "conversation_summary": summary,  # AI-generated summary of what was discussed
            "end_time": datetime.now().isoformat()
        }
        
        # Clean up: remove session from active sessions and clear memory
        del self.active_sessions[customer_id]
        self.summary_memory.clear()
        
        return session_summary

# Example usage and testing
def main():
    """
    Example usage of the banking chatbot
    
    This demonstrates:
    1. Basic chatbot usage with customer context
    2. Advanced chatbot with session management
    3. How memory and context work in practice
    """
    
    # Initialize chatbot (you'll need to provide your OpenAI API key)
    # In production, this would come from environment variables or secure config
    api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    
    # === BASIC CHATBOT DEMONSTRATION ===
    print("=== Basic Banking Chatbot ===")
    chatbot = BankingChatbot(api_key)
    
    # Set up customer context - this simulates loading customer data from a database
    customer_id = "CUST_12345"
    chatbot.set_customer_context(customer_id, {
        "company_name": "TechCorp LLC",
        "account_type": "Business Premium",
        "relationship_manager": "Sarah Johnson",
        "primary_services": ["Business Checking", "Line of Credit", "Payroll Services"]
    })

    # Simulate a customer conversation
    # Notice how later messages can reference earlier context
    messages = [
        "Hello, I need help with my business account",
        "What are the current interest rates for commercial loans?",
        "I want to increase my line of credit limit",  # This shows memory - refers back to credit services
        "Can you help me set up automated payroll transfers?"  # References payroll from context
    ]

    # Process each message and show the conversation flow
    for msg in messages:
        response = chatbot.chat(msg, customer_id)
        print(f"Customer: {msg}")
        print(f"Assistant: {response}")
        print("-" * 50)
    
    # Generate a summary of the entire conversation
    summary = chatbot.save_conversation_summary(customer_id)
    print(f"Conversation Summary: {summary}")
    
    print("\n=== Advanced Banking Chatbot with Sessions ===")
    
    # === ADVANCED CHATBOT DEMONSTRATION ===
    # Advanced chatbot with session management and better memory handling
    advanced_chatbot = AdvancedBankingChatbot(api_key)
    
    # Start a formal session with customer information
    session_id = advanced_chatbot.start_session(customer_id, {
        "company_name": "TechCorp LLC",
        "industry": "Technology",
        "annual_revenue": "$5M"
    })
    
    print(f"Started session: {session_id}")
    
    # Same conversation but with session management
    for msg in messages:
        response = advanced_chatbot.chat_with_session(msg, customer_id)
        print(f"Customer: {msg}")
        print(f"Assistant: {response}")
        print("-" * 30)
    # End the session and get comprehensive analytics
    session_summary = advanced_chatbot.end_session(customer_id)
    print(f"Session Summary: {json.dumps(session_summary, indent=2)}")

if __name__ == "__main__":
    main()
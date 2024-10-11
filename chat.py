from llm import model
from utils import get_session_id
# Import LangChain components
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, trim_messages
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

# Initialize an in-memory store to hold session histories
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create a chat history for a given session ID."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Define the chat prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Answer all questions to the best of your ability in {language}."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Set up the message trimming strategy
trimmer = trim_messages(
    max_tokens=1000,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

# Create the main runnable chain for processing messages
chain = (
    RunnablePassthrough.assign(messages=itemgetter("messages") | trimmer)
    | prompt
    | model
)

# Combine the chain with message history management
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="messages",
)

# The application is now set up and ready to handle chat sessions
def generate_response(user_input):
    # Configuration for the chat session
    config = {"configurable": {"session_id": get_session_id()}}  # Replace with a unique session ID as needed

    # Prepare the user message and the desired language
    user_message = HumanMessage(content=user_input)  # Accept user input here
    language = "English"

    # Invoke the chat model with message history management
    response = with_message_history.invoke(
        {
            "messages": [user_message],
            "language": language
        },
        config=config,
    )

    return response.content


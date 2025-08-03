import streamlit as st
from FAQ import data_ingestion, faq_chain
from sql_config import sql_chain
from pathlib import Path
from router_config import router
import random


# Load and ingest data
faqs_path = Path(__file__).parent / "resources/faq_data.csv"
data_ingestion(faqs_path)

# Set page config
st.set_page_config(page_title="🛍️ E-commerce Assistant", layout="centered")
st.title("🛍️ E-commerce ChatBot (AI)")

st.markdown("Ask about product returns, refunds, discounts, or search for products!")

def ask(query):
    query_lower = query.lower().strip()

    greetings = ["hi", "hello", "hey", "good morning", "good afternoon"]
    farewells = ["bye", "goodbye", "see you", "see ya", "take care"]
    gratitude = ["thank you", "thanks", "thankyou", "thx", "ty"]

    if query_lower in greetings:
        return "greeting", random.choice([
            "👋 Hello! How can I help you today?",
            "Hi there! 😊 What can I do for you?",
            "Hey! Ready to assist you with your shopping needs."
        ])

    if query_lower in gratitude:
        return "gratitude", random.choice([
            "🙏 You're welcome!",
            "🙌 Anytime!",
            "😊 Happy to help!",
            "👍 Let me know if you need anything else!"
        ])

    if query_lower in farewells:
        return "farewell", random.choice([
            "👋 Goodbye! Have a great day!",
            "See you soon! 🛍️",
            "Take care! 👋",
            "Hope to assist you again soon. 😊"
        ])

    # Routing logic
    result = router(query)

    if not result:
        return "unknown", "❌ Could not determine route."

    route_name = result.name.lower()

    if route_name == 'faq':
        answer = faq_chain(query)
    elif route_name == 'sql':
        answer = sql_chain(query)
    else:
        answer = f"Route `{route_name}` is not implemented."

    return route_name, answer





# Clear chat
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "👋 Hello! I'm your shopping assistant. Ask me anything."}
    ]

# Chat UI
query = st.chat_input("Write your query here...")

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("Thinking..."):
        try:
            route, response = ask(query)
        except Exception as e:
            if "Request too large" in str(e):
                route = "unknown"
                response = "❌ Your query is too large to process. Please simplify it and try again."
            else:
                route = "unknown"
                response = "❌ An unexpected error occurred while processing your query."

    feedback = f"🔍 **Intent Detected:** `{route.upper()}`"
    with st.chat_message("assistant"):
        st.markdown(response)
        st.caption(feedback)

    st.session_state.messages.append({"role": "assistant", "content": response})
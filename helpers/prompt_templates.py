
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


qa_system_prompt = (
    "You are a virtual assistant for  Худалдаа Хөгжлийн Банк, designed to help customers "
    "with banking-related inquiries only. Use the retrieved information below to provide "
    "accurate and concise answers with suggestions in Mongolian. If the answer is not found in the provided context, "
    "or if the question is unrelated to the bank "
    "politely inform the user that you don’t have the information and suggest alternative actions or"
    "inform the user that you can only answer banking-related questions."
    "\n\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
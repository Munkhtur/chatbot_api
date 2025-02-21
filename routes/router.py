import datetime
import time
from fastapi import APIRouter, Depends, FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from retrievers.combined_retriever import  get_org_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,AIMessage
from jwt import decode, exceptions
from helpers.auth import get_org_id
from models.models import ChatHistory
from helpers.db import get_db
from sqlalchemy.orm import Session
from services import services
from models.models import Chat
from helpers.scheduler import scheduler
from datetime import datetime
SECRET_KEY = "your_jwt_secret_key"  

router = APIRouter()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

INACTIVITY_TIMEOUT = 30 * 60
chat_histories = {}

class QueryRequest(BaseModel):
    user_id: str
    query: str
@router.post("/query")
async def get_response(request: QueryRequest, org_id: int = Depends(get_org_id), db:Session =Depends(get_db)):
    try:
        rag_chain = get_org_chain(org_id, db)
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception as e:
        return {"error":e}
    user_id = request.user_id
    res = []


    if user_id not in chat_histories:
        chat_histories[user_id] = ChatHistory(time_stamp=time.time(), chat=[], org_id=org_id)
    chat_history = chat_histories[user_id]

    result = rag_chain.invoke({"input": request.query, "chat_history": chat_history.chat[-20:]})
    chat_history.chat.append(HumanMessage(content=request.query))
    chat_history.chat.append(AIMessage(content=result["answer"]))

    for i, chat in enumerate(chat_history.chat[:-1]):
        if i % 2==0:
            user_message = chat  # This is the user's message
            response_message = chat_history.chat[i + 1]  # This is the AI's response (next entry)

# Assuming you want to append in this format
            res.append({"user": user_message.content, "response": response_message.content})
    print(res)
    return {
        "query": request.query,
        "response": result["answer"]
    }


@router.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id:str,  db:Session =Depends(get_db)):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
        # Validate the token
    try:
        payload = decode(token, SECRET_KEY, algorithms=["HS256"])
        org_id = payload.get("org_id")
        if not org_id:
            raise exceptions.InvalidTokenError
    except exceptions.InvalidTokenError:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    await websocket.accept()
    # user_id = str(uuid4()) 
    try:
        rag_chain = get_org_chain(org_id, db)  # Retrieve the retriever based on org_id
    except ValueError as e:
        # Send error message before closing the connection
        await websocket.send_text(f"Error: {str(e)}")
        await websocket.close(code=1008, reason=str(e))  # Send the exception message as the reason
        return
    try:
        while True:
            # Wait for the client message
            data = await websocket.receive_json()
            query = data["query"]
            max_chat_history = 10
            # Initialize chat history if not exists

            if user_id not in chat_histories:
                chat_histories[user_id] = ChatHistory(time_stamp=time.time(), chat=[], org_id=org_id)
            chat_history = chat_histories[user_id]

            # Process the RAG chain
            result = rag_chain.invoke({"input": query, "chat_history": chat_history.chat[-(max_chat_history * 2):]})

            # Update chat history
            chat_history.chat.append(HumanMessage(content=query))
            chat_history.chat.append(AIMessage(content=result["answer"]))
            # Send response back to the client
            await websocket.send_json({
                "query": query,
                "response": result["answer"]
            })

    except WebSocketDisconnect:
        # Handle disconnection
        res= []
        if user_id in chat_histories:
            chat_history = chat_histories[user_id]
            for i, chat in enumerate(chat_history.chat[:-1]):
                if i %2 == 0:
                    user_message = chat  # This is the user's message
                    response_message = chat_history.chat[i + 1]  # This is the AI's response (next entry)
                    res.append({"user": user_message.content, "response": response_message.content})
            chat_obj = Chat(
                    user_id=user_id,
                    org_id=chat_history.org_id,  # Change this if you have an organization ID
                    history=res,  # JSON structure
                )
            id = services.save_chat(obj=chat_obj, db=db)
            del chat_histories[user_id]
        print("Client disconnected")


@router.get("/chat_history")
async def get_chat_history(start_date:str= str(datetime.now().date()), end_date:str=str(datetime.now().date()),
                            org_id: int = Depends(get_org_id), db:Session =Depends(get_db)):
    chats = services.get_chat_history(org_id, start_date, end_date, db)
    return chats



@scheduler.scheduled_job("cron",minute="*/30")
def job_create_my_model_list():
    db = next(get_db())
    current_time = time.time()
    to_delete = []
    res = []
    # Check for inactive users
    for user_id, chat_history in chat_histories.items():

        # You can perform your inactivity check here and add user to the deletion list
        if current_time - chat_history.time_stamp > INACTIVITY_TIMEOUT:
            for i, chat in enumerate(chat_history.chat[:-1]):
                if i %2 == 0:
                    user_message = chat  # This is the user's message
                    response_message = chat_history.chat[i + 1]  # This is the AI's response (next entry)
                    res.append({"user": user_message.content, "response": response_message.content})
            to_delete.append(user_id)
            chat_obj = Chat(
                    user_id=user_id,
                    org_id=chat_history.org_id,  # Change this if you have an organization ID
                    history=res,  # JSON structure
                )
            id = services.save_chat(obj=chat_obj, db=db)
            print(f"Chat {id} created")
    # Delete inactive users
    for user_id in to_delete:
        del chat_histories[user_id]
        print(f"Chat history for user {user_id} deleted due to inactivity")

def setup(app: FastAPI):
    app.include_router(router)
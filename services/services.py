from datetime import datetime

from sqlalchemy.orm import Session
from models.models import Chat
from helpers.log import logging as l


def save_chat(obj:Chat, db:Session):

    try:
        db.add(obj)
        db.commit()
        # db.refresh(obj)
        return obj.id
    except Exception as e:
        l.error(f"[my model : create] ${e}")
        db.rollback()
        return None
    
def get_chat_history(org_id:int,start_date:str, end_date:str, db:Session):
    if len(start_date) == 10:  # format: YYYY-MM-DD
            start_date += " 00:00:00"
    if len(end_date) == 10:  # format: YYYY-MM-DD
        end_date += " 23:59:59"
    try:
        start_date_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        print(start_date, end_date, "services")
        chats = db.query(Chat).filter(
                    Chat.org_id == org_id,
                    Chat.created_at >= start_date_dt,
                    Chat.created_at <= end_date_dt
                                      ).all()
        return chats
    except Exception as e:
        return {"error": e}
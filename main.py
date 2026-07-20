import os
import time
from fastapi import FastAPI, Depends, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

# Import our new database modules
from database import engine, get_db
import models

load_dotenv()
client = genai.Client()
app = FastAPI()

# Command SQLAlchemy to create the tables in Neon if they don't exist yet
models.Base.metadata.create_all(bind=engine)

class UserPrompt(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"message": "Hello Architect. The AI server is online."}

def background_analytics_logger(user_text: str, ai_text: str):
    """Simulates a heavy 5-second background task like sentiment analysis or data warehousing."""
    print("\n[BACKGROUND TASK STARTED] Analyzing conversation metrics...")
    
    # Simulate a slow process (like calling another AI model)
    time.sleep(5) 
    
    word_count = len(user_text.split()) + len(ai_text.split())
    print(f"[BACKGROUND TASK COMPLETE] Conversation logged. Total words exchanged: {word_count}\n")

    
# Notice the new parameter: db: Session = Depends(get_db)
@app.post("/chat")
def chat_with_ai(prompt: UserPrompt, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # 1. RETRIEVE
        past_messages = db.query(models.Message).order_by(models.Message.id.asc()).limit(10).all()
        
        # 2. FORMAT
        history = []
        for msg in past_messages:
            role = "user" if msg.sender == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg.content}]})
            
        # 3. HYDRATE
        chat = client.chats.create(model='gemini-3.5-flash', history=history)
        
        # 4. EXECUTE (WITH RETRIES)
        max_retries = 3
        ai_text = None
        
        for attempt in range(max_retries):
            try:
                response = chat.send_message(prompt.message)
                ai_text = response.text
                break
            except Exception as e:
                if "503" in str(e) or "429" in str(e):
                    wait_time = 2 ** attempt
                    print(f"Google API overloaded. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise e
                    
        if not ai_text:
            return {"reply": "My AI brain is currently experiencing high traffic. Give me a moment and try again!"}
            
        # 5. SAVE
        user_message = models.Message(sender="user", content=prompt.message)
        db.add(user_message)
        ai_message = models.Message(sender="ai", content=ai_text)
        db.add(ai_message)
        db.commit()
        
        # 6. TRIGGER BACKGROUND TASK
        background_tasks.add_task(background_analytics_logger, prompt.message, ai_text)
        
        return {"reply": ai_text}
        
    except Exception as e:
        return {"error": str(e)}
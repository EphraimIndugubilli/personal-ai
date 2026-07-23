import os
import time
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Command SQLAlchemy to create the tables in Neon if they don't exist yet
# models.Base.metadata.create_all(bind=engine)

class UserPrompt(BaseModel):
    message: str

# 1. New schema for incoming memory requests
class MemoryRequest(BaseModel):
    text: str

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

# 2. New Endpoint: The Memory Bank
@app.post("/remember/")
def store_memory(request: MemoryRequest, db: Session = Depends(get_db)):
    # Create a new memory object (Ensure models.Memory exists in your models.py!)
    content = request.text.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Memory text cannot be empty.")

    new_memory = models.Memory(content=content)
    
    # Save it to the Neon database
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)
    
    return {
        "status": "Success",
        "message": "The Architect has logged this to long-term memory.",
        "memory_id": new_memory.id,
        "content": new_memory.content
    }


@app.get("/memories")
def list_memories(db: Session = Depends(get_db)):
    """Return saved long-term memories, newest first."""
    memories = (
        db.query(models.Memory)
        .order_by(models.Memory.timestamp.desc(), models.Memory.id.desc())
        .all()
    )

    return [
        {"id": memory.id, "content": memory.content, "timestamp": memory.timestamp}
        for memory in memories
    ]


@app.put("/memories/{memory_id}")
def update_memory(memory_id: int, request: MemoryRequest, db: Session = Depends(get_db)):
    """Replace one saved memory."""
    memory = db.get(models.Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")

    content = request.text.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Memory text cannot be empty.")

    memory.content = content
    db.commit()
    db.refresh(memory)

    return {"id": memory.id, "content": memory.content, "timestamp": memory.timestamp}


@app.delete("/memories/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    """Permanently delete one saved memory."""
    memory = db.get(models.Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")

    db.delete(memory)
    db.commit()

    return {"status": "Success", "message": "Memory deleted.", "memory_id": memory_id}

# Notice the new parameter: db: Session = Depends(get_db)
@app.post("/chat")
def chat_with_ai(prompt: UserPrompt, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # 1. RETRIEVE: load the latest conversation turns and personal memories.
        past_messages = (
            db.query(models.Message)
            .order_by(models.Message.id.desc())
            .limit(10)
            .all()
        )
        past_messages.reverse()

        memories = (
            db.query(models.Memory)
            .order_by(models.Memory.timestamp.desc(), models.Memory.id.desc())
            .limit(5)
            .all()
        )
        memory_context = "\n".join(f"- {memory.content}" for memory in memories)
        
        # 2. FORMAT
        history = []
        for msg in past_messages:
            role = "user" if msg.sender == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg.content}]})
            
        # 3. HYDRATE
        chat = client.chats.create(model=GEMINI_MODEL, history=history)

        message_for_model = prompt.message
        if memory_context:
            message_for_model = (
                "Use these saved long-term memories as personal context when relevant. "
                "Do not claim to know anything beyond them.\n\n"
                f"Saved memories:\n{memory_context}\n\n"
                f"Current user message: {prompt.message}"
            )
        
        # 4. EXECUTE (WITH RETRIES)
        max_retries = 3
        ai_text = None
        
        for attempt in range(max_retries):
            try:
                response = chat.send_message(message_for_model)
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

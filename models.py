from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

# We are creating a table called "messages"
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True)  # This will store either 'user' or 'ai'
    content = Column(String)
    # The database will automatically stamp the exact time the message was created
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
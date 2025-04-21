# # app/models/chat.py
# from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from ..database import Base, User

# class Conversation(Base):
#     __tablename__ = "conversations"
    
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     title = Column(String(255), default="New Conversation")
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
#     # Define relationships
#     user = relationship("User", backref="conversations")
#     messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
#     posts = relationship("SocialMediaPost", back_populates="conversation", cascade="all, delete-orphan")

# class Message(Base):
#     __tablename__ = "messages"
    
#     id = Column(Integer, primary_key=True, index=True)
#     conversation_id = Column(Integer, ForeignKey("conversations.id"))
#     role = Column(String(50))  # user, assistant, system
#     content = Column(Text)
#     created_at = Column(DateTime, default=datetime.utcnow)
    
#     # Define relationships
#     conversation = relationship("Conversation", back_populates="messages")


# app/models/chat.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    user = relationship("User", backref="conversations")
    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan")
    # posts relationship is defined in the SocialMediaPost model

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(50))  # user, assistant, system
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
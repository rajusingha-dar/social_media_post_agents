# app/models/post.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON  # Import JSON type
import enum
import json
from datetime import datetime
from ..database import Base

class PlatformType(str, enum.Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    REDDIT = "reddit"

class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    platform = Column(String(20))  # Using String instead of Enum for simplicity
    content = Column(Text)
    draft_versions = Column(Text, default="{}")  # Store as JSON string
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships with backref
    user = relationship("User", backref="posts")
    conversation = relationship("Conversation", backref="posts")
    
    # Helper methods for JSON handling
    def get_draft_versions(self):
        """Get draft versions as a dictionary."""
        try:
            return json.loads(self.draft_versions)
        except:
            return {}
    
    def set_draft_versions(self, versions_dict):
        """Set draft versions from a dictionary."""
        self.draft_versions = json.dumps(versions_dict)
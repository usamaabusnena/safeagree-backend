# safeagree_backend/database/models.py
# Defines SQLAlchemy ORM models for the SafeAgree application.

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import sqlalchemy.orm
from werkzeug.security import generate_password_hash, check_password_hash

# Base for declarative models
Base = sqlalchemy.orm.declarative_base()


class User(Base):
    """
    SQLAlchemy model for the 'users' table.
    Stores user authentication and profile information.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False) # Stores hashed and salted password

    # Relationship to UserPolicy table
    user_policies = relationship("UserPolicy", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hashes the given password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User(email='{self.email}')>"
    
    def serialize(self):
        """Serializes the user object to a dictionary."""
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns},
        data.pop('password_hash'),  # Exclude password hash from serialization
        return data
        

class Policy(Base):
    """
    SQLAlchemy model for the 'policies' table.
    Stores metadata about processed privacy policies.
    """
    __tablename__ = 'policies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False) # Company name associated with the policy
    policy_hash = Column(String(64), unique=True, nullable=False) # FNV1-a hash of the policy text
    result_file_name = Column(String(255), nullable=False) # Name/key of the JSON file in S3
    processing_date = Column(DateTime, default=datetime.now(), nullable=False) # Date/time of processing
    original_link = Column(String(512), nullable=True) # Original URL of the policy if applicable
    # Relationship to UserPolicy table
    user_policies = relationship("UserPolicy", back_populates="policy", cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<Policy(id={self.id}, company_name='{self.company_name}', "
                f"processing_date='{self.processing_date}...')>")

class UserPolicy(Base):
    """
    SQLAlchemy model for the 'user_policies' table.
    Represents the many-to-many relationship between users and policies (user's library).
    """
    __tablename__ = 'user_policies'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    policy_id = Column(Integer, ForeignKey('policies.id'), primary_key=True)

    user = relationship("User", back_populates="user_policies")
    policy = relationship("Policy", back_populates="user_policies")

    def __repr__(self):
        return f"<UserPolicy(user_id={self.user_id}, policy_id={self.policy_id})>"
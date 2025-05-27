# --- 1. database.py ---
# This file defines the SQLAlchemy models for the User, Policy, and UserPolicy tables,
# and provides functions for interacting with the MySQL database.

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy.orm
from database.models import Base, User, Policy, UserPolicy # Import models

from config import Config  # Import configuration settings

class DatabaseManager:
    """
    Manages all database interactions for the SafeAgree application.
    Encapsulates SQLAlchemy engine, session, and CRUD operations.
    """
    def __init__(self, database_url=None):
        # Determine the initial database_url from argument or environment variable
        effective_db_url = Config.DATABASE_URL if database_url is None else database_url
        # If no URL is found, set a default and print a message
        if not effective_db_url:
            print("DATABASE_URL environment variable not set or provided. Using default PostgreSQL connection.")
            # Example for PostgreSQL running locally (replace with your actual credentials/host)
            # Make sure you have 'psycopg2-binary' installed for PostgreSQL dialect
            effective_db_url = "postgresql://myuser:mypw@localhost:5432/safeagree_db"
            # For a production setup, NEVER hardcode credentials like this. Use environment variables!
        
        # Store the determined URL in the instance and use it for the engine
        self.database_url = effective_db_url
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)


    def create_tables(self):
        """Creates all defined tables in the database."""
        try:
            Base.metadata.create_all(self.engine)
            print("Database tables created successfully.")
        except SQLAlchemyError as e:
            print(f"Error creating database tables: {e}")

    def add_user(self, email, password):
        """Adds a new user to the database."""
        session = self.Session()
        try:
            new_user = User(email=email)
            new_user.set_password(password)
            session.add(new_user)
            session.commit()
            return new_user
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error adding user: {e}")
            return None
        finally:
            session.close()

    def get_user_by_email(self, email):
        """Retrieves a user by their email address."""
        session = self.Session()
        try:
            return session.query(User).filter_by(email=email).first()
        except SQLAlchemyError as e:
            print(f"Error getting user by email: {e}")
            return None
        finally:
            session.close()

    def get_user_by_id(self, user_id):
        """Retrieves a user by their ID."""
        session = self.Session()
        try:
            return session.query(User).filter_by(id=user_id).first()
        except SQLAlchemyError as e:
            print(f"Error getting user by ID: {e}")
            return None
        finally:
            session.close()

    def update_user_password(self, user_id, new_password):
        """Updates a user's password."""
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.set_password(new_password)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error updating user password: {e}")
            return False
        finally:
            session.close()

    def delete_user(self, user_id):
        """Deletes a user and their associated policies from the database."""
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error deleting user: {e}")
            return False
        finally:
            session.close()

    def add_policy(self, company_name, original_link, policy_hash, result_file_name):
        """Adds a new policy's metadata to the database."""
        session = self.Session()
        try:
            new_policy = Policy(
                company_name=company_name,
                original_link=original_link,
                policy_hash=policy_hash,
                result_file_name=result_file_name,
            )
            session.add(new_policy)
            session.commit()
            return new_policy
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error adding policy: {e}")
            return None
        finally:
            session.close()

    def get_policy_by_hash(self, policy_hash):
        """Retrieves a policy by its content hash."""
        session = self.Session()
        try:
            return session.query(Policy).filter_by(policy_hash=policy_hash).first()
        except SQLAlchemyError as e:
            print(f"Error getting policy by hash: {e}")
            return None
        finally:
            session.close()

    def get_policy_by_id(self, policy_id):
        """Retrieves a policy by its ID."""
        session = self.Session()
        try:
            return session.query(Policy).filter_by(id=policy_id).first()
        except SQLAlchemyError as e:
            print(f"Error getting policy by ID: {e}")
            return None
        finally:
            session.close()

    def add_user_policy(self, user_id, policy_id):
        """Links a policy to a user's library."""
        session = self.Session()
        try:
            # Check if the association already exists
            existing_link = session.query(UserPolicy).filter_by(
                user_id=user_id, policy_id=policy_id
            ).first()
            if existing_link:
                print(f"Policy {policy_id} already in user {user_id}'s library.")
                return existing_link

            new_user_policy = UserPolicy(user_id=user_id, policy_id=policy_id)
            session.add(new_user_policy)
            session.commit()
            return new_user_policy
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error adding policy to user library: {e}")
            return None
        finally:
            session.close()

    def remove_user_policy(self, user_id, policy_id):
        """Removes a policy from a user's library."""
        session = self.Session()
        try:
            user_policy_link = session.query(UserPolicy).filter_by(
                user_id=user_id, policy_id=policy_id
            ).first()
            if user_policy_link:
                session.delete(user_policy_link)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error removing policy from user library: {e}")
            return False
        finally:
            session.close()

    def get_policies_for_user(self, user_id):
        """Retrieves all policies associated with a specific user's library."""
        session = self.Session()
        try:
            # Join UserPolicy with Policy to get full policy details
            policies = session.query(Policy).join(UserPolicy).filter(UserPolicy.user_id == user_id).all()
            return policies
        except SQLAlchemyError as e:
            print(f"Error getting policies for user: {e}")
            return []
        finally:
            session.close()

    def get_all_policies(self):
        """Retrieves all policies that have been processed."""
        session = self.Session()
        try:
            # Order by evaluation date in descending order for most recent first
            return session.query(Policy).order_by(Policy.processing_date.desc()).all()
        except SQLAlchemyError as e:
            print(f"Error getting all policies: {e}")
            return []
        finally:
            session.close()

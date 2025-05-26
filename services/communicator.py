# --- 3. communicator.py ---
# This file defines the Communicator component, acting as the central orchestration hub.
# It handles policy processing, history checks, and coordination with AI models, Database, and Filebase.


#### from webdriver_manager.firefox import GeckoDriverManager  # Uncomment for real scraping
import time
from io import BytesIO
import fnvhash
import hashlib
import json
import os
from datetime import datetime
from urllib.parse import urlparse
import PyPDF2
from docx import Document
import re

# Assuming database.py and filebase.py are in the same directory or accessible via PYTHONPATH
from database.crud import DatabaseManager
from services.file_storage_service import FilebaseManager

class Communicator:
    """
    The central orchestration hub for SafeAgree backend.
    Manages policy processing, history checks, and coordination with AI models, Database, and Filebase.
    """
    def __init__(self, db_manager: DatabaseManager, fb_manager: FilebaseManager):
        self.db_manager = db_manager
        self.fb_manager = fb_manager
        # self.tokenizer = AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer") # For real Llama Tokenizer

    def _calculate_hash(self, text):
        """Calculates hash of the policy text."""
        return fnvhash.fnv1a_64(text.encode('utf-8'))  # Using FNV-1a for a quick hash, can be replaced if needed

    def segment_text_oop115_style(text: str) -> list[str]:
        """
        Segments a given text (e.g., a privacy policy) into segments that are closer
        to paragraphs or list items, as described for the OOP115 dataset.

        The segmentation strategy involves:
        1. Initial segmentation into paragraphs by splitting on double newlines.
        2. Within each paragraph, checking for common list item patterns (numbered lists,
        bullet points). If found, the paragraph is further segmented into individual
        list items.
        3. If no list patterns are found, the paragraph itself is considered a segment.
        4. Trimming whitespace from each resulting segment.

        Args:
            text: The input text string to be segmented.

        Returns:
            A list of strings, where each string is a segmented paragraph or list item.
        """
        if not text:
            return []

        # Step 1: Segment into paragraphs by splitting on double newlines.
        # This handles most natural paragraph breaks.
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        segmented_output = []
        for paragraph in paragraphs:
            # Define common list item patterns.
            # This regex looks for:
            # - Numbered lists (e.g., "1.", "2.", "1)", "2)")
            # - Bullet points (e.g., "-", "*", "•" - common unicode bullet)
            # It captures the list item content after the marker.
            list_item_pattern = re.compile(r'^\s*(?:(?:\d+\.|\d+\)|\*|-|•)\s+)(.*)', re.MULTILINE)

            # Find all potential list items within the current paragraph
            list_items = []
            last_end = 0
            for match in list_item_pattern.finditer(paragraph):
                # If there's text before the current list item that isn't a list item itself,
                # add it as a separate segment (e.g., introductory sentence to a list)
                pre_list_text = paragraph[last_end:match.start()].strip()
                if pre_list_text:
                    segmented_output.append(pre_list_text)

                list_items.append(match.group(0).strip()) # Capture the full matched item
                last_end = match.end()

            # If list items were found, add them to the output
            if list_items:
                segmented_output.extend(list_items)
                # Add any remaining text after the last list item in the paragraph
                remaining_text = paragraph[last_end:].strip()
                if remaining_text:
                    segmented_output.append(remaining_text)
            else:
                # If no list items were found, the entire paragraph is a segment
                segmented_output.append(paragraph)

        # Final cleanup to ensure no empty strings are left
        return [s for s in segmented_output if s]
# --- End of Helper function ---

    # IMPLEMENT!!!!!!!!!!!
    def _call_summarizer_ai(self, tokenized_text):
        """
        Mocks the call to the Summarizer AI model.
        Returns dummy annotations (summary).
        """
        print("MOCK: Calling Summarizer AI.")
        # In a real scenario, this would be an API call to your AI model endpoint
        # Example:
        # response = requests.post("http://summarizer-ai-service/summarize", json={"text": tokenized_text})
        # return response.json()
        return {
            "summary_sections": [
                {"title": "Data Collection", "content": "We collect personal data like name, email, and usage patterns."},
                {"title": "Data Usage", "content": "Data is used for service improvement, personalization, and marketing."},
                {"title": "Data Sharing", "content": "We may share data with third-party partners for analytics and advertising."},
                {"title": "User Rights", "content": "You have rights to access, correct, and delete your data, subject to limitations."},
                {"title": "Security Measures", "content": "We implement security measures to protect your data, but cannot guarantee absolute security."}
            ],
            "key_points": [
                "Extensive data collection.",
                "Data sharing with third parties.",
                "Limited user control over data."
            ],
            "overall_sentiment": "Neutral with potential privacy concerns."
        }

    def process_policy(self, user_id, policy_input, input_type, company_name, file_extension=None):
        """
        Main function to process a privacy policy.
        Handles history check, AI summarization, and storage.
        :param user_id: ID of the user initiating the request.
        :param policy_input: URL (if input_type='link') or file content (if input_type='file').
        :param input_type: 'link' or 'file'.
        :param company_name: Optional company name for the policy.
        :param processing_date: Required processing date for the policy (datetime.date object).
        :return: Tuple (policy_object, summary_data) or (None, error_message)
        """

        policy_text = None
        if input_type == 'link':
            original_link = policy_input
            policy_text = self._scrape_policy_text(policy_input)
            # Try to infer company name from URL if not provided
            if not company_name:
                try:
                    parsed_url = urlparse(policy_input)
                    company_name = parsed_url.netloc.split('.')[0] # e.g., 'google' from 'www.google.com'
                except Exception:
                    company_name = "Unknown Company"
        elif input_type == 'file':
            policy_text = self._read_policy_file(policy_input)
            if not company_name:
                company_name = "Uploaded File Policy"
        else:
            return None, "Invalid input type. Must be 'link' or 'file'."

        if not policy_text:
            return None, "Failed to retrieve policy text."

        policy_hash = self.calculate_hash(policy_text)
        existing_policy = self.db_manager.get_policy_by_hash(policy_hash)

        summary_data = None
        policy_obj = None

        if existing_policy:
            # update processing date if it exists
            existing_policy.processing_date = datetime.now()
            # Policy already processed, retrieve from S3
            print(f"Policy with hash {policy_hash} found in history. Retrieving summary from S3.")
            summary_data = self.fb_manager.get_json_from_s3(existing_policy.result_file_name)
            policy_obj = existing_policy
            if not summary_data:
                print(f"WARNING: Summary file {existing_policy.result_file_name} not found in S3 despite DB entry.")
                # If S3 file is missing, re-process (optional, depending on error handling strategy)
                # For now, we'll just return an error if S3 retrieval fails.
                return None, "Cached summary not found in storage."
        else:
            # New policy, process with AI
            print(f"New policy. Processing with AI.")
            tokenized_text = self._tokenize_text(policy_text)
            raw_annotations = self._call_summarizer_ai(tokenized_text)
            summary_data = self._organize_annotations(raw_annotations)

            # Generate a unique file name for S3
            s3_file_name = f"policy_summary_{policy_hash}.json"
            if not self.fb_manager.upload_json_to_s3(s3_file_name, summary_data):
                return None, "Failed to upload summary to file storage."

            # Store policy metadata in DB
            policy_obj = self.db_manager.add_policy(
                company_name=company_name,
                original_link=original_link if input_type == 'link' else None,
                processing_date=datetime.now(),
                policy_hash=policy_hash,
                result_file_name=s3_file_name
            )
            if not policy_obj:
                return None, "Failed to save policy metadata to database."

        # Automatically add to user's history/library
        self.db_manager.add_user_policy(user_id, policy_obj.id)

        return policy_obj, summary_data

    def add_policy_to_library(self, user_id, policy_id):
        """Adds an existing processed policy to a user's library."""
        user = self.db_manager.get_user_by_id(user_id)
        policy = self.db_manager.get_policy_by_id(policy_id)
        if not user:
            return False, "User not found."
        if not policy:
            return False, "Policy not found."
        if self.db_manager.add_user_policy(user_id, policy_id):
            return True, "Policy added to library."
        return False, "Failed to add policy to library (might already be there)."

    def get_user_library(self, user_id):
        """
        Retrieves all policies in a user's library.
        :param user_id: The ID of the user.
        :return: List of dictionaries, each containing policy id and company name.
        """
        policies_metadata = self.db_manager.get_policies_for_user(user_id)
        library_items = []
        for policy in policies_metadata:
            library_items.append({
                "policy_id": policy.id,
                "company_name": policy.company_name,
            })
        return library_items

    def update_user_library(self, user_id):
        """
        Checks for newer versions of policies in a user's library and re-summarizes if needed.
        This is a simplified mock. In a real scenario, you'd need to store the original URL
        or file path to re-scrape/re-read the content.
        For demonstration, we'll just simulate an update for existing policies.
        """
        print(f"MOCK: Updating library for user {user_id}. This is a placeholder for re-scraping and re-summarization.")
        user_policies = self.db_manager.get_policies_for_user(user_id) # Get policies linked to user
        
        for policy in user_policies:
            policy_link = policy.original_link
            if not policy_link:
                print(f"The Privacy Policy  for {policy.company_name} has no original link. Skipping update check.")
                continue
            else:
                updated_policy, summary = self.process_policy(user_id, policy_link, input_type='link', company_name=policy.company_name)
                self.remove_policy_from_library(user_id, policy.id)  # Remove old version
                self.add_policy_to_library(user_id, updated_policy.id)  # Add updated version
                print(f"Successfully updated policy {policy.company_name}.")
        user_policies = self.get_user_library(user_id)
        return user_policies

    def remove_policy_from_library(self, user_id, policy_id):
        """Removes a policy from a user's library."""
        return self.db_manager.remove_user_policy(user_id, policy_id)

    def import_user_library(self, user_id, file_content):
        """
        Imports policies from a file containing policy links.
        Each link is processed through the summarization flow.
        """
        imported_links = file_content.splitlines()
        results = []
        for link in imported_links:
            link = link.strip()
            if link:
                policy_obj, summary_data = self.process_policy(user_id, link, input_type='link')
                if policy_obj:
                    results.append({"link": link, "status": "success", "policy_id": policy_obj.id})
                    #add to user's library
                    self.db_manager.add_user_policy(user_id, policy_obj.id)
                else:
                    print(f"Failed to process link {link}: {summary_data}")
                    results.append({"link": link, "status": "error", "message": summary_data})
        user_policies = self.get_user_library(user_id)
        return results, user_policies

    '''deprecated
    def export_user_library(self, user_id):
        """
        Exports a user's library as a list of policy links (mocked).
        In a real scenario, you'd need to store the original URLs or have a way to reconstruct them.
        """
        policies = self.db_manager.get_policies_for_user(user_id)
        links = []
        for policy in policies:
            if policy.original_link:
                links.append(policy.original_link)
            else:
                print(f"Policy {policy.id} ({policy.company_name}) has no original link. Skipping export.")
        # Here you would typically return the links or save them to a file
        new_file_name = f"user_{user_id}_library_links.txt"
        with open(new_file_name, 'w') as f:
            for link in links:
                f.write(f"{link}\n")
        print(f"Exported user library to {new_file_name}.")
        f.close()
        return new_file_name
        '''

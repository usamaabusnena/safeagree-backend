# safeagree_backend/routes/policy_routes.py
# Defines API endpoints for policy summarization and library management.

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import re
from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity, create_refresh_token
import os
import json # For parsing JSON from S3, if needed directly
import datetime
from urllib.parse import urlparse
# We'll need to pass the communicator instance to these routes from app.py
from flask import Blueprint
policy_bp = Blueprint('policy', __name__, url_prefix='/policy')


communicator_instance = None # This will be set by app.py
db_manager_instance = None # This will be set by app.py
filebase_manager_instance = None # This will be set by app.py


def set_policy_communicator(communicator):
    global communicator_instance
    communicator_instance = communicator

def set_policy_managers(db_manager, filebase_manager):
    global db_manager_instance, filebase_manager_instance
    db_manager_instance = db_manager
    filebase_manager_instance = filebase_manager

# --- Policy Summarization and Library Management Endpoints ---

@policy_bp.route("/summarize", methods=["POST"])
@jwt_required()
def summarize_policy():
    """
    Endpoint to summarize a privacy policy from a link or uploaded file.
    Expects 'policy_input' (URL or file content) and 'input_type' ('link' or 'file').
    """
    user_id = get_jwt_identity()
    input_type = request.form.get("input_type") # Use form for file uploads
    processing_date = datetime.now()
    policy_input = None
    if input_type == 'link':
        policy_input = request.form.get("policy_link")
        if not policy_input:
            return jsonify({"message": "Missing 'policy_link' for link input type."}), 404
        
        # find the company name from the URL
        parsed_url = urlparse(policy_input)
        domain_parts = parsed_url.netloc.split('.')
        if len(domain_parts) >= 2:
        # Common case: example.com, www.example.com, sub.example.com
        # Take the second to last part (e.g., 'example' from 'example.com' or 'sub.example.com')
            company_name = domain_parts[-2]
        elif len(domain_parts) == 1:
            # Case: localhost, or a single-word domain
            company_name = domain_parts[0]
        else:
            company_name = "Unknown Company" # Should not happen with valid URLs

    elif input_type == 'file':
        if 'policy_file' not in request.files:
            return jsonify({"message": "Missing 'policy_file' for file input type."}), 404
        file = request.files['policy_file']
        if file.filename == '':
            return jsonify({"message": "No selected file."}), 400
        policy_input = file.read() # Read file content as bytes
        if not policy_input:
            return jsonify({"message": "Empty file content."}), 400
        # Extract file extension from filename
        if '.' in file.filename:
            file_extension = file.filename.rsplit('.', 1)[1].lower()
        else:
            return jsonify({"message": "Missing 'file extension' for file input type."}), 400
        # find the company name from the file name
        base_name = os.path.splitext(file.filename)[0]
        company_name = re.sub(r'(_|\s)?(privacy|policy|terms|conditions|agreement)(_|\s)?', '', base_name, flags=re.IGNORECASE).strip()
    else:
        return jsonify({"message": "Invalid 'input_type'. Must be 'link' or 'file'."}), 400

    policy_obj, summary_data = communicator_instance.process_policy(
        user_id, policy_input, input_type, company_name, processing_date, file_extension if input_type == 'file' else None
    )

    if policy_obj and summary_data:
        return jsonify({
            "message": "Policy processed successfully",
            "policy_id": policy_obj.id,
            "original_link": policy_obj.original_link if policy_obj.original_link else None,
            "company_name": policy_obj.company_name,
            "summary": summary_data
        }), 200
    return jsonify({"message": summary_data or "Failed to process policy."}), 500


@policy_bp.route("/<int:policy_id>", methods=["GET"])
def get_policy_details(policy_id):
    """
    Endpoint to retrieve full details of a specific policy by its ID.
    This endpoint is used by PolicyDetail.tsx and ComparePolicies.tsx.
    """

    policy = db_manager_instance.get_policy_by_id(policy_id)
    if not policy:
        return jsonify({"message": "Policy not found."}), 404

    summary_data = filebase_manager_instance.get_json_from_s3(policy.result_file_name)
    if not summary_data:
        return jsonify({"message": "Summary data not found for this policy."}), 422

    return jsonify({
        "company_name": policy.company_name,
        "original_link": policy.original_link if policy.original_link else None,
        "summary": summary_data,
        "processing_date": policy.processing_date
    }), 200


# --- User Library Management Endpoints ---

@policy_bp.route("/library/add/<int:policy_id>", methods=["POST"])
@jwt_required()
def add_to_library(policy_id):
    """Endpoint to add a processed policy to the user's library."""
    user_id = get_jwt_identity()
    success, message = communicator_instance.add_policy_to_library(user_id, policy_id)
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"message": message}), 400

@policy_bp.route("/library/view", methods=["GET"])
@jwt_required()
def view_library():
    """Endpoint to view all policies in the user's library."""
    user_id = get_jwt_identity()
    library_items = communicator_instance.get_user_library(user_id)
    return jsonify(library=library_items), 200

@policy_bp.route("/library/update", methods=["POST"])
@jwt_required()
def update_library():
    """Endpoint to update policies in the user's library (check for new versions)."""
    user_id = get_jwt_identity()
    updated_policies = communicator_instance.update_user_library(user_id)
    return jsonify(message="Library updated succesfully.", updated_policies=updated_policies), 200

@policy_bp.route("/library/remove/<int:policy_id>", methods=["DELETE"])
@jwt_required()
def remove_from_library(policy_id):
    """Endpoint to remove a policy from the user's library."""
    user_id = get_jwt_identity()
    if communicator_instance.remove_policy_from_library(user_id, policy_id):
        return jsonify({"message": "Policy removed from library."}), 200
    return jsonify({"message": "Failed to remove policy or policy not found in library."}), 404

@policy_bp.route("/library/import", methods=["POST"])
@jwt_required()
def import_library():
    """Endpoint to import policies from an uploaded text file containing links."""
    user_id = get_jwt_identity()
    if 'import_file' not in request.files:
        return jsonify({"message": "No import_file provided."}), 400
    
    file = request.files['import_file']
    if file.filename == '':
        return jsonify({"message": "No selected file."}), 400
    
    file_content = file.read().decode('utf-8')
    import_results, user_policies = communicator_instance.import_user_library(user_id, file_content)
    
    return jsonify(message="Library import initiated.", results=import_results, library=user_policies), 200


@policy_bp.route("/public-history", methods=["GET"]) # Changed from /history/public to /policy/public-history
def get_public_history():
    """
    Endpoint to retrieve a list of all processed policies for public viewing.
    Does NOT require authentication.
    """
    if not db_manager_instance or not filebase_manager_instance:
        return jsonify({"message": "Backend managers not initialized."}), 500

    all_policies = db_manager_instance.get_all_policies()
    
    public_history_list = []
    for policy in all_policies:

        public_history_list.append({
            "id": policy.id,
            "company_name": policy.company_name,
            "original_link": policy.original_link if policy.original_link else None,
            "processing_date": policy.processing_date.isoformat()
        })
    
    return jsonify(history=public_history_list), 200


'''deprecated

@policy_bp.route("/library/export", methods=["GET"])
@jwt_required()
def export_library():
    """Endpoint to export the user's library as a text file of links."""
    user_id = get_jwt_identity()
    export_content = communicator_instance.export_user_library(user_id)
    # Flask will automatically set Content-Type to text/plain and handle download
    return export_content, 200, {'Content-Disposition': 'attachment; filename=safeagree_library.txt'}
'''

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from services.documents import extract_document_text
from services.rag import delete_document, index_document, list_documents

documents_bp = Blueprint("documents", __name__)
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@documents_bp.route("/api/documents", methods=["GET", "POST"])
@jwt_required()
def documents():
    username = str(get_jwt_identity())
    if request.method == "GET":
        return jsonify({"documents": list_documents(username)})

    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"error": "Choose a PDF, TXT, or Markdown file"}), 400
    filename = secure_filename(upload.filename)
    if not filename or "." + filename.rsplit(".", 1)[-1].lower() not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Only PDF, TXT, and Markdown files are supported"}), 400
    try:
        text = extract_document_text(filename, upload.read())
        count = index_document(username, filename, text)
    except (ValueError, UnicodeError) as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Could not extract or index this document"}), 422
    return jsonify({"source": filename, "chunks": count}), 201


@documents_bp.delete("/api/documents/<path:source_name>")
@jwt_required()
def remove_document(source_name):
    if not delete_document(str(get_jwt_identity()), secure_filename(source_name)):
        return jsonify({"error": "Document not found"}), 404
    return jsonify({"deleted": True})

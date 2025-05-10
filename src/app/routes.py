from flask import Blueprint, request, jsonify
from .services import ingest_csv_data
from .models import db, Wallet # Import Wallet to allow querying if needed in routes

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the Crypto Intel Platform API"}), 200

@main_bp.route("/ingest", methods=["POST"])
def handle_ingest_csv():
    # For MVP, we assume the file is already at a known location or path is passed in request
    # In a production app, this would handle file uploads securely.
    data = request.get_json()
    csv_path = data.get("csv_path") if data else None
    
    if csv_path:
        result = ingest_csv_data(csv_path=csv_path)
    else:
        # Use default path if none provided in request
        result = ingest_csv_data() 
        
    if result.get("status") == "success":
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@main_bp.route("/wallets", methods=["GET"])
def get_wallets():
    try:
        wallets = Wallet.query.all()
        wallets_data = [
            {
                "id": w.id,
                "wallet_address": w.wallet_address,
                "initial_extraction_confidence": w.initial_extraction_confidence,
                "first_seen_csv": w.first_seen_csv,
                "last_updated_csv": w.last_updated_csv,
                "composite_scam_score": w.composite_scam_score,
                "last_enriched_at": w.last_enriched_at.isoformat() if w.last_enriched_at else None,
                "last_scored_at": w.last_scored_at.isoformat() if w.last_scored_at else None
            } for w in wallets
        ]
        return jsonify(wallets_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route("/wallets/<string:wallet_address_param>", methods=["GET"])
def get_wallet_details(wallet_address_param):
    try:
        wallet = Wallet.query.filter_by(wallet_address=wallet_address_param).first()
        if not wallet:
            return jsonify({"error": "Wallet not found"}), 404
        
        wallet_data = {
            "id": wallet.id,
            "wallet_address": wallet.wallet_address,
            "initial_extraction_confidence": wallet.initial_extraction_confidence,
            "first_seen_csv": wallet.first_seen_csv,
            "last_updated_csv": wallet.last_updated_csv,
            "composite_scam_score": wallet.composite_scam_score,
            "last_enriched_at": wallet.last_enriched_at.isoformat() if wallet.last_enriched_at else None,
            "last_scored_at": wallet.last_scored_at.isoformat() if wallet.last_scored_at else None,
            "groups": [g.group_name for g in wallet.groups],
            "enrichment_data": [
                {
                    "source_api": ed.source_api,
                    "attribute_name": ed.attribute_name,
                    "attribute_value": ed.attribute_value,
                    "retrieved_at": ed.retrieved_at.isoformat() if ed.retrieved_at else None
                } for ed in wallet.enrichment_data
            ],
            "score_components": [
                {
                    "component_name": sc.component_name,
                    "component_score_contribution": sc.component_score_contribution,
                    "details": sc.details
                } for sc in wallet.score_components
            ]
        }
        return jsonify(wallet_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add more routes for enrichment and scoring triggers as needed


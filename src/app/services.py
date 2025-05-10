import csv
import os
from datetime import datetime
from flask import Flask # For the __main__ example
from .models import db, Wallet, WalletGroup # Assuming models are defined in models.py

def ingest_csv_data(csv_path="upload/crypto_wallet_data.csv"):
    """
    Processes the input CSV to extract relevant columns for wallet addresses and group information,
    and populates the database using pure Python CSV handling.
    Returns a summary of the ingestion process.
    """
    processed_count = 0
    added_count = 0
    updated_count = 0
    error_count = 0
    errors = []

    try:
        with open(csv_path, mode='r', encoding='latin1', newline='') as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            print(f"Successfully read CSV: {csv_path} with headers: {headers}")

            if not headers:
                errors.append(f"CSV file {csv_path} is empty or has no headers.")
                return {
                    "status": "error",
                    "message": "CSV file is empty or has no headers.",
                    "processed_count": 0,
                    "added_count": 0,
                    "updated_count": 0,
                    "error_count": 1,
                    "errors": errors
                }

            id_column_name = headers[0]
            wallet_address_column_name = "WalletAddress"
            group_column_name = "Groups"

            required_columns = [id_column_name, wallet_address_column_name]
            for col in required_columns:
                if col not in headers:
                    errors.append(f"Missing required column: {col} in {csv_path}")
                    return {
                        "status": "error",
                        "message": f"Missing required column: {col}",
                        "processed_count": 0,
                        "added_count": 0,
                        "updated_count": 0,
                        "error_count": 1,
                        "errors": errors
                    }
            
            row_number = 1 
            for row in reader:
                row_number += 1
                processed_count += 1
                try:
                    wallet_id = str(row[id_column_name])
                    wallet_address = str(row[wallet_address_column_name])
                    
                    if not wallet_address:
                        errors.append(f"Skipped row {row_number} due to missing wallet address.")
                        error_count += 1
                        continue

                    wallet_entry = Wallet.query.filter_by(wallet_address=wallet_address).first()
                    
                    initial_confidence_str = row.get("InitialConfidence", "0.0")
                    try:
                        initial_confidence = float(initial_confidence_str) if initial_confidence_str else 0.0
                    except ValueError:
                        initial_confidence = 0.0 
                        errors.append(f"Warning: Could not parse InitialConfidence on row {row_number} (value: {initial_confidence_str}). Defaulting to 0.0.")

                    if not wallet_entry:
                        wallet_entry = Wallet(
                            id=wallet_id, 
                            wallet_address=wallet_address,
                            initial_extraction_confidence=initial_confidence,
                            first_seen_csv=str(datetime.utcnow()),
                            last_updated_csv=str(datetime.utcnow())
                        )
                        db.session.add(wallet_entry)
                        added_count += 1
                    else:
                        wallet_entry.last_updated_csv = str(datetime.utcnow())
                        updated_count += 1
                    
                    if group_column_name in headers and row.get(group_column_name):
                        group_names_str = str(row[group_column_name])
                        group_list = [group.strip() for group in group_names_str.split(';') if group.strip()]
                        
                        for group_name in group_list:
                            wallet_group = WalletGroup.query.filter_by(wallet_address=wallet_address, group_name=group_name).first()
                            if not wallet_group:
                                wallet_group = WalletGroup(wallet_address=wallet_address, group_name=group_name)
                                db.session.add(wallet_group)
                    
                    db.session.commit()

                except Exception as e:
                    db.session.rollback()
                    error_count += 1
                    errors.append(f"Error processing row {row_number} (ID: {row.get(id_column_name, 'N/A')}): {str(e)}")
        
        return {
            "status": "success", 
            "message": "CSV data ingestion complete.",
            "processed_count": processed_count,
            "added_count": added_count,
            "updated_count": updated_count,
            "error_count": error_count,
            "errors": errors
        }

    except FileNotFoundError:
        errors.append(f"Error: The file {csv_path} was not found.")
        return {"status": "error", "message": f"File not found: {csv_path}", "errors": errors, "error_count": 1, "processed_count": 0, "added_count": 0, "updated_count": 0}
    except Exception as e:
        errors.append(f"An unexpected error occurred during CSV ingestion: {str(e)}")
        return {"status": "error", "message": f"Unexpected error: {str(e)}", "errors": errors, "error_count": 1, "processed_count": 0, "added_count": 0, "updated_count": 0}

if __name__ == '__main__':
    app = Flask(__name__)
    # Corrected path for instance folder and site.db, assuming backend/app/services.py structure
    instance_folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    if not os.path.exists(instance_folder_path):
        os.makedirs(instance_folder_path)
    db_path = os.path.join(instance_folder_path, 'site.db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_csv_path = os.path.join(backend_dir, 'upload', 'extracted_wallet_group_data.csv')
        
        if not os.path.exists(sample_csv_path):
            os.makedirs(os.path.join(backend_dir, 'upload'), exist_ok=True)
            # Simplified dummy CSV creation for testing
            dummy_header = ["ID","WalletAddress","Groups","InitialConfidence"]
            dummy_rows = [
                ["1","0x123abc","ScamGroupA;PhishGroupB","0.8"],
                ["2","0x456def","ScamGroupA","0.5"],
                ["3","0x789ghi","GoodGroupC","0.1"],
                ["4","0xInvalidAddress","","0.0"] # Example with empty group and address
            ]
            with open(sample_csv_path, mode='w', newline='', encoding='latin1') as f:
                writer = csv.writer(f)
                writer.writerow(dummy_header)
                writer.writerows(dummy_rows)
            print(f"Created dummy CSV for testing at: {sample_csv_path}")

        print(f"Attempting to ingest: {sample_csv_path}")
        ingestion_result = ingest_csv_data(csv_path=sample_csv_path)
        print(ingestion_result)


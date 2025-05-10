from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Wallet(db.Model):
    __tablename__ = "wallets"
    id = db.Column(db.String, primary_key=True) # Assuming ID from CSV is the primary key
    wallet_address = db.Column(db.String, unique=True, nullable=False)
    initial_extraction_confidence = db.Column(db.Float)
    first_seen_csv = db.Column(db.String) # Or db.DateTime if converting
    last_updated_csv = db.Column(db.String) # Or db.DateTime if converting
    composite_scam_score = db.Column(db.Float)
    last_enriched_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_scored_at = db.Column(db.DateTime, default=datetime.utcnow)

    groups = db.relationship("WalletGroup", backref="wallet", lazy=True)
    enrichment_data = db.relationship("EnrichmentData", backref="wallet", lazy=True)
    score_components = db.relationship("ScoreComponent", backref="wallet", lazy=True)

    def __repr__(self):
        return f"<Wallet {self.wallet_address}>"

class WalletGroup(db.Model):
    __tablename__ = "wallet_groups"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wallet_address = db.Column(db.String, db.ForeignKey("wallets.wallet_address"), nullable=False)
    group_name = db.Column(db.String, nullable=False)
    group_confidence_score = db.Column(db.Float) # Derived

    def __repr__(self):
        return f"<WalletGroup {self.wallet_address} - {self.group_name}>"

class EnrichmentData(db.Model):
    __tablename__ = "enrichment_data"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wallet_address = db.Column(db.String, db.ForeignKey("wallets.wallet_address"), nullable=False)
    source_api = db.Column(db.String, nullable=False)
    attribute_name = db.Column(db.String, nullable=False)
    attribute_value = db.Column(db.Text) # Using Text for flexibility, can be JSON string
    retrieved_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EnrichmentData {self.wallet_address} - {self.source_api} - {self.attribute_name}>"

class ScoreComponent(db.Model):
    __tablename__ = "score_components"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wallet_address = db.Column(db.String, db.ForeignKey("wallets.wallet_address"), nullable=False)
    component_name = db.Column(db.String, nullable=False)
    component_score_contribution = db.Column(db.Float)
    details = db.Column(db.Text) # Using Text for flexibility, can be JSON string

    def __repr__(self):
        return f"<ScoreComponent {self.wallet_address} - {self.component_name}>"


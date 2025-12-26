"""
HIPAA-SAFE AI Training Database
Stores only de-identified, aggregated data for future AI risk scoring.
NO PHI (patient names, IDs, dates) is stored.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import os

DB_PATH = 'ai_training_data.db'

def init_database():
    """Initialize SQLite database with HIPAA-safe schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # HIPAA-SAFE: Only aggregate/hashed data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payer_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_date TIMESTAMP,
        payer_name TEXT,
        cpt_code TEXT,
        state TEXT,
        denial_code TEXT,
        rarc_code TEXT,
        recoverability_status TEXT,
        adjustment_amount DECIMAL,
        claim_hash TEXT
    )
    ''')
    
    # Analytics aggregates (for dashboard)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analytics_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        calculation_date TIMESTAMP,
        payer_name TEXT,
        cpt_code TEXT,
        total_claims INTEGER,
        total_denied_amount DECIMAL,
        avg_denial_amount DECIMAL,
        top_denial_code TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def anonymize_patient_data(patient_name, claim_id):
    """Hash PHI to create non-reversible identifiers"""
    if not patient_name or patient_name == 'N/A':
        return 'ANON_' + hashlib.sha256(str(claim_id).encode()).hexdigest()[:12]
    
    # Create hash from patient name + claim (STABLE - no date)
    combined = f"{patient_name}_{claim_id}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def save_ai_training_data(df):
    """
    Save HIPAA-safe data for AI training.
    Removes all PHI before storage.
    Detects and skips duplicates based on claim_hash.
    """
    if len(df) == 0:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create anonymized dataset
    safe_df = pd.DataFrame()
    safe_df['upload_date'] = datetime.now()
    safe_df['payer_name'] = df.get('payer_name', 'Unknown')
    safe_df['cpt_code'] = df.get('cpt_code', 'Unknown')
    safe_df['state'] = df.get('state', 'Unknown')
    safe_df['denial_code'] = df['code_display']
    safe_df['rarc_code'] = df.get('rarc', '')
    safe_df['recoverability_status'] = df.get('recoverability', 'REVIEW_REQUIRED')
    safe_df['adjustment_amount'] = df['amount']
    
    # Hash claim IDs (not reversible)
    safe_df['claim_hash'] = df.apply(
        lambda row: anonymize_patient_data(
            row.get('patient', 'N/A'), 
            row.get('claim_id', 'UNK')
        ), 
        axis=1
    )
    
    # ===== DUPLICATE DETECTION =====
    # Get existing claim hashes from database
    try:
        cursor.execute('SELECT DISTINCT claim_hash FROM payer_performance')
        existing_hashes = {row[0] for row in cursor.fetchall()}
    except:
        existing_hashes = set()
    
    # Filter out duplicates
    safe_df['is_duplicate'] = safe_df['claim_hash'].isin(existing_hashes)
    new_claims = safe_df[~safe_df['is_duplicate']].drop(columns=['is_duplicate'])
    duplicates_count = len(safe_df) - len(new_claims)
    
    # Save only new claims
    if len(new_claims) > 0:
        new_claims.to_sql('payer_performance', conn, if_exists='append', index=False)
    
    conn.close()
    
    return len(new_claims), duplicates_count

def get_payer_stats():
    """Get aggregated payer performance for AI insights"""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    query = '''
    SELECT 
        payer_name,
        COUNT(*) as total_denials,
        SUM(adjustment_amount) as total_denied,
        AVG(adjustment_amount) as avg_denial,
        denial_code,
        COUNT(denial_code) as denial_count
    FROM payer_performance
    GROUP BY payer_name, denial_code
    ORDER BY total_denied DESC
    LIMIT 100
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_training_dataset_size():
    """Return count of records in AI training database"""
    if not os.path.exists(DB_PATH):
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM payer_performance')
    count = cursor.fetchone()[0]
    conn.close()
    return count

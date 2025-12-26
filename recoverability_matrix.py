# Velden Vault - Recoverability Matrix (Sales-Ready)
# Maps ALL CARC codes to professional status labels for client-facing reports

import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Professional display labels (NOT database-style)
STATUS_DISPLAY = {
    "VELDEN_FIXABLE": "✓ Recoverable (Priority)",
    "RESCUE_CANDIDATE": "⚡ Rescue Candidate (HFS 1624)",
    "FATAL_PREVENTION": "☠️ Fatal (Prevention Required)",
    "PARTIALLY_RECOVERABLE": "◐ Conditionally Recoverable",
    "UNRECOVERABLE": "✗ Process Failure",
    "PATIENT_RESPONSIBILITY": "💰 Patient Balance",
    "CONTRACTUAL": "📋 Contractual Write-off",
    "REVIEW_REQUIRED": "🔍 Review Required",
}

# CSS classes for styling
STATUS_COLORS = {
    "VELDEN_FIXABLE": "#00d4aa",  # Green
    "RESCUE_CANDIDATE": "#f39c12",  # Orange/Gold - ONLY CO-29
    "FATAL_PREVENTION": "#c0392b",  # Dark Red - Sell Roster Sentinel
    "PARTIALLY_RECOVERABLE": "#3498db",  # Blue
    "UNRECOVERABLE": "#e74c3c",  # Red
    "PATIENT_RESPONSIBILITY": "#9b59b6",  # Purple
    "CONTRACTUAL": "#95a5a6",  # Gray
    "REVIEW_REQUIRED": "#f1c40f",  # Yellow
}

def get_display_status(status_code):
    """Convert internal status code to professional client-facing label"""
    return STATUS_DISPLAY.get(status_code, status_code)

def get_status_color(status_code):
    """Get the display color for a status"""
    return STATUS_COLORS.get(status_code, "#ffffff")

def load_full_recoverability_matrix():
    """Load ALL CARC codes with SALES-READY classifications"""
    
    # IMPORTANT: CO-29 is Velden's SPECIALTY (HFS 1624 Automator)
    # It is NOT unrecoverable - it's a RESCUE CANDIDATE
    
    MANUAL_CLASSIFICATIONS = {
        # PATIENT RESPONSIBILITY
        "1": {"status": "PATIENT_RESPONSIBILITY", "category": "Deductible", "fixable": False, "action": "Bill patient for deductible amount"},
        "2": {"status": "PATIENT_RESPONSIBILITY", "category": "Coinsurance", "fixable": False, "action": "Bill patient for coinsurance amount"},
        "3": {"status": "PATIENT_RESPONSIBILITY", "category": "Copay", "fixable": False, "action": "Bill patient for copay amount"},
        "66": {"status": "PATIENT_RESPONSIBILITY", "category": "Blood Deductible", "fixable": False, "action": "Bill patient"},
        
        # VELDEN FIXABLE - Priority Recovery
        "4": {"status": "VELDEN_FIXABLE", "category": "Modifier Error", "fixable": True, "action": "Correct modifier settings in EHR and resubmit"},
        "5": {"status": "VELDEN_FIXABLE", "category": "Place of Service", "fixable": True, "action": "Update POS code and resubmit"},
        "6": {"status": "VELDEN_FIXABLE", "category": "Age Inconsistency", "fixable": True, "action": "Verify patient DOB and resubmit"},
        "7": {"status": "VELDEN_FIXABLE", "category": "Gender Inconsistency", "fixable": True, "action": "Verify patient gender and resubmit"},
        "8": {"status": "VELDEN_FIXABLE", "category": "Taxonomy Error", "fixable": True, "action": "Update provider taxonomy code in EHR"},
        "9": {"status": "VELDEN_FIXABLE", "category": "Diagnosis Age", "fixable": True, "action": "Review diagnosis for age appropriateness"},
        "10": {"status": "VELDEN_FIXABLE", "category": "Diagnosis Gender", "fixable": True, "action": "Review diagnosis for gender coding"},
        "11": {"status": "VELDEN_FIXABLE", "category": "Diagnosis/Procedure", "fixable": True, "action": "Match diagnosis to procedure code"},
        "12": {"status": "VELDEN_FIXABLE", "category": "Provider Type", "fixable": True, "action": "Update provider credentials"},
        "15": {"status": "VELDEN_FIXABLE", "category": "Modifier Error", "fixable": True, "action": "Update or match modifier to procedure code"},
        "16": {"status": "VELDEN_FIXABLE", "category": "Missing Info", "fixable": True, "action": "Add missing claim information and resubmit"},
        "22": {"status": "PARTIALLY_RECOVERABLE", "category": "COB Issue", "fixable": True, "action": "Verify coordination of benefits"},
        "31": {"status": "PARTIALLY_RECOVERABLE", "category": "Eligibility", "fixable": True, "action": "Verify patient eligibility and resubmit"},
        "96": {"status": "VELDEN_FIXABLE", "category": "Non-Covered", "fixable": True, "action": "Review coding alternatives"},
        "109": {"status": "VELDEN_FIXABLE", "category": "Wrong Payer", "fixable": True, "action": "Submit to correct payer"},
        "140": {"status": "VELDEN_FIXABLE", "category": "ID Mismatch", "fixable": True, "action": "Verify patient ID and name spelling"},
        "146": {"status": "VELDEN_FIXABLE", "category": "Diagnosis Error", "fixable": True, "action": "Update diagnosis code"},
        "167": {"status": "VELDEN_FIXABLE", "category": "Diagnosis Issue", "fixable": True, "action": "Review diagnosis coding"},
        "170": {"status": "VELDEN_FIXABLE", "category": "Provider Type", "fixable": True, "action": "Update provider type/specialty"},
        "171": {"status": "VELDEN_FIXABLE", "category": "Facility Type", "fixable": True, "action": "Update facility type"},
        "172": {"status": "VELDEN_FIXABLE", "category": "Specialty", "fixable": True, "action": "Update provider specialty"},
        "173": {"status": "VELDEN_FIXABLE", "category": "Prescription", "fixable": True, "action": "Obtain prescription documentation"},
        "181": {"status": "VELDEN_FIXABLE", "category": "Procedure Invalid", "fixable": True, "action": "Update procedure code"},
        "182": {"status": "VELDEN_FIXABLE", "category": "Modifier Invalid", "fixable": True, "action": "Correct modifier code"},
        "183": {"status": "VELDEN_FIXABLE", "category": "Referring Provider", "fixable": True, "action": "Add referring provider NPI"},
        "184": {"status": "VELDEN_FIXABLE", "category": "Ordering Provider", "fixable": True, "action": "Add ordering provider NPI"},
        "185": {"status": "VELDEN_FIXABLE", "category": "Rendering Provider", "fixable": True, "action": "Verify rendering provider credentials"},
        "199": {"status": "VELDEN_FIXABLE", "category": "Revenue/Procedure", "fixable": True, "action": "Match revenue code to procedure"},
        "206": {"status": "VELDEN_FIXABLE", "category": "NPI Missing", "fixable": True, "action": "Add provider NPI"},
        "207": {"status": "VELDEN_FIXABLE", "category": "NPI Invalid", "fixable": True, "action": "Correct NPI format"},
        "208": {"status": "VELDEN_FIXABLE", "category": "NPI Mismatch", "fixable": True, "action": "Update NPI enrollment"},
        "226": {"status": "VELDEN_FIXABLE", "category": "Provider Info", "fixable": True, "action": "Submit required provider documentation"},
        "227": {"status": "VELDEN_FIXABLE", "category": "Patient Info", "fixable": True, "action": "Submit required patient documentation"},
        "252": {"status": "VELDEN_FIXABLE", "category": "Attachment Required", "fixable": True, "action": "Submit required attachment"},
        "282": {"status": "VELDEN_FIXABLE", "category": "Type of Bill", "fixable": True, "action": "Correct type of bill code"},
        
        # CONTRACTUAL - Normal business adjustments
        "45": {"status": "CONTRACTUAL", "category": "Fee Schedule", "fixable": False, "action": "Contractual write-off per fee schedule"},
        "97": {"status": "CONTRACTUAL", "category": "Bundled", "fixable": False, "action": "Service bundled with primary procedure"},
        "59": {"status": "CONTRACTUAL", "category": "Multiple Procedure", "fixable": False, "action": "Multiple procedure reduction applied"},
        "44": {"status": "CONTRACTUAL", "category": "Prompt Pay", "fixable": False, "action": "Prompt pay discount applied"},
        
        # ===============================================
        # RESCUE CANDIDATES - ONLY CO-29 Timely Filing
        # HFS 1624 is EXCLUSIVELY for timely filing!
        # ===============================================
        "29": {
            "status": "RESCUE_CANDIDATE", 
            "category": "Timely Filing", 
            "fixable": True, 
            "action": "HFS 1624 Override - Retroactive Eligibility Appeal"
        },
        
        # ===============================================
        # FATAL PREVENTION - Sells Roster Sentinel
        # These CANNOT be rescued - use to sell retainer
        # ===============================================
        "197": {
            "status": "FATAL_PREVENTION", 
            "category": "Auth Missing", 
            "fixable": False, 
            "action": "PREVENTION: Install Roster Sentinel to catch pre-cert requirements"
        },
        "198": {
            "status": "FATAL_PREVENTION", 
            "category": "Auth Exceeded", 
            "fixable": False, 
            "action": "PREVENTION: Roster Sentinel tracks auth unit limits"
        },
        
        # TRUE UNRECOVERABLE - Only when absolutely no recourse
        "18": {"status": "UNRECOVERABLE", "category": "Duplicate", "fixable": False, "action": "Exact duplicate - already paid"},
        "26": {"status": "UNRECOVERABLE", "category": "Pre-Coverage", "fixable": False, "action": "Service before coverage effective date"},
        "27": {"status": "UNRECOVERABLE", "category": "Post-Coverage", "fixable": False, "action": "Service after coverage terminated"},
        "35": {"status": "UNRECOVERABLE", "category": "Lifetime Max", "fixable": False, "action": "Lifetime benefit exhausted"},
        "39": {"status": "FATAL_PREVENTION", "category": "Auth Denied", "fixable": False, "action": "PREVENTION: Roster Sentinel pre-auth workflow"},
        "50": {"status": "UNRECOVERABLE", "category": "Medical Necessity", "fixable": False, "action": "Requires clinical appeal - low success rate"},
        "55": {"status": "UNRECOVERABLE", "category": "Experimental", "fixable": False, "action": "Experimental/investigational procedure"},
        "119": {"status": "UNRECOVERABLE", "category": "Benefit Max", "fixable": False, "action": "Period benefit maximum reached"},
        "149": {"status": "UNRECOVERABLE", "category": "Lifetime Max", "fixable": False, "action": "Lifetime service maximum reached"},
        "204": {"status": "UNRECOVERABLE", "category": "Not Covered", "fixable": False, "action": "Service not covered under plan"},
    }
    
    # Load CARC CSV
    carc_paths = [
        os.path.join(SCRIPT_DIR, 'Claim Adjustment Reason Codes(CARC).csv'),
        os.path.join(SCRIPT_DIR, 'Claim Adjustment Reason Codes(CARC) - Sheet1.csv'),
    ]
    
    full_matrix = {}
    
    for path in carc_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                code_col = [c for c in df.columns if 'CODE' in c.upper() and 'DESC' not in c.upper()][0]
                desc_col = [c for c in df.columns if 'DESC' in c.upper()][0]
                
                for _, row in df.iterrows():
                    code = str(row[code_col]).strip()
                    desc = str(row[desc_col]).strip()
                    if '\n' in desc:
                        desc = desc.split('\n')[0]
                    
                    if code in MANUAL_CLASSIFICATIONS:
                        info = MANUAL_CLASSIFICATIONS[code].copy()
                        info['description'] = desc
                    else:
                        info = auto_classify_code(code, desc)
                    
                    full_matrix[code] = info
                break
            except Exception as e:
                print(f"Error loading CARC CSV: {e}")
    
    return full_matrix

def auto_classify_code(code, description):
    """Automatically classify a code based on its description"""
    desc_lower = description.lower()
    
    # Patient responsibility keywords
    patient_keywords = ['deductible', 'coinsurance', 'copay', 'co-pay', 'patient responsibility']
    for keyword in patient_keywords:
        if keyword in desc_lower:
            return {
                "status": "PATIENT_RESPONSIBILITY",
                "category": "Patient Balance",
                "fixable": False,
                "action": "Bill patient for applicable amount",
                "description": description
            }
    
    # Rescue candidate - ONLY for timely filing (CO-29)
    # DO NOT mark authorization issues as rescue!
    timely_keywords = ['timely', 'time limit', 'filing deadline']
    for keyword in timely_keywords:
        if keyword in desc_lower and 'authorization' not in desc_lower and 'precert' not in desc_lower:
            return {
                "status": "RESCUE_CANDIDATE",
                "category": "Timely Filing",
                "fixable": True,
                "action": "HFS 1624 Override Appeal",
                "description": description
            }
    
    # Authorization issues = FATAL PREVENTION (sell Roster Sentinel)
    auth_keywords = ['authorization', 'precertification', 'precert', 'pre-cert', 'prior auth']
    for keyword in auth_keywords:
        if keyword in desc_lower:
            return {
                "status": "FATAL_PREVENTION",
                "category": "Authorization",
                "fixable": False,
                "action": "PREVENTION: Install Roster Sentinel",
                "description": description
            }
    
    # Truly unrecoverable
    unrecoverable_keywords = ['expired', 'terminated', 'maximum', 'lifetime', 'not covered', 
                               'experimental', 'investigational', 'duplicate']
    for keyword in unrecoverable_keywords:
        if keyword in desc_lower:
            return {
                "status": "UNRECOVERABLE",
                "category": "Policy Limit",
                "fixable": False,
                "action": "No recovery path available",
                "description": description
            }
    
    # Contractual keywords
    contractual_keywords = ['fee schedule', 'contractual', 'bundled', 'included in', 'allowance']
    for keyword in contractual_keywords:
        if keyword in desc_lower:
            return {
                "status": "CONTRACTUAL",
                "category": "Contractual",
                "fixable": False,
                "action": "Standard contractual adjustment",
                "description": description
            }
    
    # Fixable keywords - Velden can recover
    fixable_keywords = ['missing', 'invalid', 'incomplete', 'incorrect', 'lacks',
                        'not provided', 'billing error', 'submission error',
                        'modifier', 'taxonomy', 'npi', 'identifier', 'provider',
                        'diagnosis', 'procedure code', 'coding']
    for keyword in fixable_keywords:
        if keyword in desc_lower:
            return {
                "status": "VELDEN_FIXABLE",
                "category": "Billing Issue",
                "fixable": True,
                "action": "Correct and resubmit claim",
                "description": description
            }
    
    # Default: needs review
    return {
        "status": "REVIEW_REQUIRED",
        "category": "Unknown",
        "fixable": None,
        "action": "Manual review required",
        "description": description
    }

# Load the full matrix
RECOVERABILITY = load_full_recoverability_matrix()
DEFAULT_STATUS = {
    "status": "REVIEW_REQUIRED", 
    "category": "Unknown", 
    "fixable": None, 
    "action": "Manual review required",
    "description": "Code not found"
}

def get_recoverability(carc_code: str) -> dict:
    """Get recoverability status for a CARC code"""
    return RECOVERABILITY.get(str(carc_code).strip(), DEFAULT_STATUS)

def get_recovery_summary(denials_df):
    """Calculate recovery potential with SALES-READY categories"""
    
    results = {
        "VELDEN_FIXABLE": {"count": 0, "amount": 0.0, "label": "✓ Recoverable (Priority)", "color": "#00d4aa"},
        "RESCUE_CANDIDATE": {"count": 0, "amount": 0.0, "label": "⚡ Rescue Candidate", "color": "#f39c12"},
        "PARTIALLY_RECOVERABLE": {"count": 0, "amount": 0.0, "label": "◐ Conditionally Recoverable", "color": "#3498db"},
        "UNRECOVERABLE": {"count": 0, "amount": 0.0, "label": "✗ Process Failure", "color": "#e74c3c"},
        "PATIENT_RESPONSIBILITY": {"count": 0, "amount": 0.0, "label": "💰 Patient Balance", "color": "#9b59b6"},
        "CONTRACTUAL": {"count": 0, "amount": 0.0, "label": "📋 Contractual", "color": "#95a5a6"},
        "REVIEW_REQUIRED": {"count": 0, "amount": 0.0, "label": "🔍 Review Required", "color": "#f1c40f"},
    }
    
    for _, row in denials_df.iterrows():
        code = str(row.get('reason_code', '')).split('-')[-1] if '-' in str(row.get('reason_code', '')) else str(row.get('reason_code', ''))
        rec_info = get_recoverability(code)
        status = rec_info['status']
        amount = float(row.get('amount', 0) or 0)
        
        if status in results:
            results[status]['count'] += 1
            results[status]['amount'] += amount
    
    return results

# Print summary
if __name__ == "__main__":
    print(f"\n✓ Loaded {len(RECOVERABILITY)} CARC codes (SALES-READY)")
    
    status_counts = {}
    for code, info in RECOVERABILITY.items():
        status = info.get('status', 'UNKNOWN')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nClassification Summary:")
    for status, count in sorted(status_counts.items()):
        display = get_display_status(status)
        print(f"  {display}: {count} codes")

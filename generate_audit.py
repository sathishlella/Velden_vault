# Velden Vault - 835 Denial Anatomy Audit Engine
# Core parsing script for analyzing 835 ERA files

import pandas as pd
import os
from edi_835_parser import parse

# --- STEP 1: LOAD THE "BRAINS" (CARC/RARC Dictionaries) ---
print("\n" + "="*50)
print("  VELDEN VAULT | Denial Anatomy Audit Engine")
print("="*50)
print("\nLoading Intelligence Modules...")

script_dir = os.path.dirname(os.path.abspath(__file__))

# Load CARC (Claim Adjustment Reason Codes)
carc_map = {}
carc_paths = [
    os.path.join(script_dir, 'Claim Adjustment Reason Codes(CARC).csv'),
    os.path.join(script_dir, 'Claim Adjustment Reason Codes(CARC) - Sheet1.csv'),
]
for path in carc_paths:
    if os.path.exists(path):
        try:
            carc_df = pd.read_csv(path)
            code_col = [c for c in carc_df.columns if 'CODE' in c.upper() and 'DESC' not in c.upper()][0]
            desc_col = [c for c in carc_df.columns if 'DESC' in c.upper()][0]
            for _, row in carc_df.iterrows():
                code = str(row[code_col]).strip()
                desc = str(row[desc_col]).strip()
                if '\n' in desc:
                    desc = desc.split('\n')[0]
                carc_map[code] = desc
            print(f"✓ CARC Database Loaded ({len(carc_map)} codes)")
            break
        except Exception as e:
            print(f"⚠ Error loading CARC: {e}")

# Load RARC (Remittance Advice Remark Codes)
rarc_map = {}
rarc_paths = [
    os.path.join(script_dir, 'Remittance Advice Remark Codes(RARC).csv'),
    os.path.join(script_dir, 'Remittance Advice Remark Codes(RARC) - Sheet1.csv'),
]
for path in rarc_paths:
    if os.path.exists(path):
        try:
            rarc_df = pd.read_csv(path)
            code_col = [c for c in rarc_df.columns if 'CODE' in c.upper() and 'DESC' not in c.upper()][0]
            desc_col = [c for c in rarc_df.columns if 'DESC' in c.upper()][0]
            for _, row in rarc_df.iterrows():
                code = str(row[code_col]).strip()
                desc = str(row[desc_col]).strip()
                if '\n' in desc:
                    desc = desc.split('\n')[0]
                rarc_map[code] = desc
            print(f"✓ RARC Database Loaded ({len(rarc_map)} codes)")
            break
        except Exception as e:
            print(f"⚠ Error loading RARC: {e}")

# Load Recoverability Matrix
try:
    from recoverability_matrix import RECOVERABILITY, DEFAULT_STATUS, get_recoverability
    print("✓ Recoverability Matrix Loaded")
except ImportError:
    print("⚠ Recoverability Matrix not found, using basic mode")
    RECOVERABILITY = {}
    DEFAULT_STATUS = {"status": "REVIEW_REQUIRED", "category": "Unknown", "fixable": None}
    def get_recoverability(code):
        return DEFAULT_STATUS

# --- STEP 2: THE CRAWLER ---
denial_records = []
input_folder = os.path.join(script_dir, 'client_data')

print(f"\nScanning client files in: {input_folder}")
if not os.path.exists(input_folder):
    os.makedirs(input_folder)
    print(f"✓ Created '{input_folder}' folder")
    print("  Put your .835 files in there and run again.")
    print("  Or run: python mock_835_generator.py to create test data")
    exit()

files_found = 0
for filename in os.listdir(input_folder):
    if filename.endswith('.835') or filename.endswith('.txt') or filename.endswith('.edi'):
        files_found += 1
        filepath = os.path.join(input_folder, filename)
        try:
            remittance = parse(filepath)
            
            for transaction in remittance.transaction_sets:
                for claim in transaction.claims:
                    # Access adjustments at SERVICE level (not claim level)
                    if hasattr(claim, 'services') and claim.services:
                        for service in claim.services:
                            if hasattr(service, 'adjustments') and service.adjustments:
                                for adj in service.adjustments:
                                    # Get group code and reason code
                                    group_code = str(adj.group_code.code) if hasattr(adj.group_code, 'code') else str(adj.group_code)
                                    reason_code = str(adj.reason_code.code) if hasattr(adj.reason_code, 'code') else str(adj.reason_code)
                                    
                                    if group_code in ['CO', 'PR', 'OA', 'PI']:
                                        # Get CARC description
                                        desc_carc = carc_map.get(reason_code, "Unknown Reason")
                                        
                                        # Get recoverability info
                                        rec_info = get_recoverability(reason_code)
                                        
                                        # Get amount
                                        amount = float(adj.amount) if hasattr(adj, 'amount') and adj.amount else 0.0
                                        
                                        # Build record
                                        denial_records.append({
                                            'File': filename,
                                            'Patient': getattr(claim, 'patient_name', 'N/A'),
                                            'Claim_ID': getattr(claim, 'claim_id', 'N/A'),
                                            'Service_Date': getattr(claim, 'service_date', 'N/A'),
                                            'Code': f"{group_code}-{reason_code}",
                                            'Description': desc_carc[:80] if desc_carc else 'N/A',
                                            'Amount': amount,
                                            'Status': rec_info['status'],
                                            'Fixable': rec_info.get('fixable', None),
                                            'Recovery_Action': rec_info.get('description', 'Review required')
                                        })
        except Exception as e:
            print(f"⚠ Skipping {filename}: {e}")

if files_found == 0:
    print("\n✗ No .835 files found in ./client_data/")
    print("  Run: python mock_835_generator.py to create test data")
    exit()

print(f"✓ Processed {files_found} files, found {len(denial_records)} adjustment records")

# --- STEP 3: THE FORENSIC REPORT ---
if denial_records:
    df = pd.DataFrame(denial_records)
    
    # Aggregate by Code
    summary = df.groupby(['Code', 'Description', 'Status'])['Amount'].agg(['sum', 'count']).reset_index()
    summary.columns = ['Code', 'Description', 'Status', 'Total_Amount', 'Count']
    summary = summary.sort_values(by='Total_Amount', ascending=False)
    
    # Calculate recovery potential
    fixable_total = df[df['Status'] == 'VELDEN_FIXABLE']['Amount'].sum()
    unrecoverable_total = df[df['Status'] == 'UNRECOVERABLE']['Amount'].sum()
    total_denied = df['Amount'].sum()
    
    print("\n" + "="*60)
    print("  VELDEN VAULT | FORENSIC DENIAL AUDIT REPORT")
    print("="*60)
    
    print(f"\n💰 TOTAL DENIED AMOUNT:     ${total_denied:>15,.2f}")
    print(f"✅ VELDEN CAN RECOVER:      ${fixable_total:>15,.2f}  ({fixable_total/total_denied*100:.1f}%)" if total_denied > 0 else "")
    print(f"❌ UNRECOVERABLE:           ${unrecoverable_total:>15,.2f}  ({unrecoverable_total/total_denied*100:.1f}%)" if total_denied > 0 else "")
    
    print("\n" + "-"*60)
    print("  TOP 10 DENIAL REASONS BY REVENUE IMPACT")
    print("-"*60)
    
    # Format for display
    display_summary = summary.head(10).copy()
    display_summary['Total_Amount'] = display_summary['Total_Amount'].apply(lambda x: f"${x:,.2f}")
    print(display_summary.to_string(index=False))
    
    # Save detailed report
    output_file = os.path.join(script_dir, "Velden_Forensic_Report.csv")
    df.to_csv(output_file, index=False)
    
    # Save summary
    summary_file = os.path.join(script_dir, "Velden_Summary_Report.csv")
    summary.to_csv(summary_file, index=False)
    
    print("\n" + "-"*60)
    print(f"✓ Detailed report saved: {output_file}")
    print(f"✓ Summary report saved:  {summary_file}")
    print("-"*60)
    
    print("\n📊 Run the Streamlit dashboard for interactive analysis:")
    print("   streamlit run app.py")
    print()
else:
    print("\n✗ No denial records found in these files.")
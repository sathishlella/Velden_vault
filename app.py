# Velden Vault - 835 Denial Anatomy Audit Dashboard
# Streamlit application for analyzing ERA files

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import tempfile
import base64
from datetime import datetime

# Import AI training database (HIPAA-safe)
try:
    from database import init_database, save_ai_training_data, get_training_dataset_size
    DATABASE_ENABLED = True
except ImportError:
    DATABASE_ENABLED = False
    print("⚠️ Database module not found - AI data collection disabled")

# ============================================================================
# AUTHENTICATION SYSTEM
# ============================================================================
def check_password():
    """Returns True if user entered correct password"""
    
    def password_entered():
        """Checks whether password is correct"""
        try:
            if (st.session_state["username"] == st.secrets["passwords"]["admin_username"] and
                st.session_state["password"] == st.secrets["passwords"]["admin_password"]):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store password
                del st.session_state["username"]   # Don't store username
            else:
                st.session_state["password_correct"] = False
        except Exception as e:
            st.session_state["password_correct"] = False
            st.error(f"Authentication error: {e}")

    # First run - show login
    if "password_correct" not in st.session_state:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h1 style='color: #00d4aa;'>🔐 VELDEN VAULT</h1>
            <p style='color: #888; font-size: 1.1rem;'>Forensic Revenue Recovery System</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("👤 Username", key="username", placeholder="Enter username")
            st.text_input("🔑 Password", type="password", key="password", placeholder="Enter password")
            st.button("🚀 Login", on_click=password_entered, use_container_width=True)
        
        st.markdown("---")
        st.info("💡 **Demo Credentials:** Contact administrator for access")
        return False
    
    # Password incorrect
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h1 style='color: #00d4aa;'>🔐 VELDEN VAULT</h1>
            <p style='color: #888; font-size: 1.1rem;'>Forensic Revenue Recovery System</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.error("❌ Invalid credentials. Please try again.")
            st.text_input("👤 Username", key="username", placeholder="Enter username")
            st.text_input("🔑 Password", type="password", key="password", placeholder="Enter password")
            st.button("🚀 Login", on_click=password_entered, use_container_width=True)
        return False
    
    # Password correct
    else:
        return True

# Page configuration
st.set_page_config(
    page_title="Velden Vault | Denial Anatomy Audit",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Velden Health branding
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --velden-dark: #0a0f1a;
        --velden-primary: #00d4aa;
        --velden-secondary: #1a2744;
        --velden-accent: #00b894;
        --velden-text: #e0e6ed;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0a0f1a 0%, #1a2744 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 4px solid #00d4aa;
    }
    
    .main-header h1 {
        color: #00d4aa;
        margin: 0;
        font-weight: 700;
    }
    
    .main-header p {
        color: #8892a0;
        margin: 0.5rem 0 0 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a2744 0%, #0d1829 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2d3a52;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4aa;
    }
    
    .metric-label {
        color: #8892a0;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Status badges */
    .badge-fixable {
        background: #00d4aa;
        color: #0a0f1a;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    .badge-unrecoverable {
        background: #e74c3c;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    .badge-review {
        background: #f39c12;
        color: #0a0f1a;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    /* Code lookup section */
    .code-lookup-box {
        background: linear-gradient(135deg, #1a2744 0%, #0d1829 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2d3a52;
    }
    
    .stTextInput > div > div {
        background-color: #0d1829;
        border: 1px solid #2d3a52;
        border-radius: 8px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #1a2744 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e6ed;
    }
</style>
""", unsafe_allow_html=True)

# Load CARC/RARC dictionaries
@st.cache_data
def load_code_dictionaries():
    """Load CARC and RARC code dictionaries from CSV files"""
    carc_map = {}
    rarc_map = {}
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to load CARC
    carc_paths = [
        os.path.join(script_dir, 'Claim Adjustment Reason Codes(CARC).csv'),
        os.path.join(script_dir, 'Claim Adjustment Reason Codes(CARC) - Sheet1.csv'),
    ]
    for path in carc_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                # Handle different column name formats
                code_col = [c for c in df.columns if 'CODE' in c.upper() and 'DESC' not in c.upper()][0]
                desc_col = [c for c in df.columns if 'DESC' in c.upper()][0]
                for _, row in df.iterrows():
                    code = str(row[code_col]).strip()
                    desc = str(row[desc_col]).strip()
                    # Clean up description (take first line only)
                    if '\n' in desc:
                        desc = desc.split('\n')[0]
                    carc_map[code] = desc
                break
            except Exception as e:
                st.warning(f"Error loading CARC: {e}")
    
    # Try to load RARC
    rarc_paths = [
        os.path.join(script_dir, 'Remittance Advice Remark Codes(RARC).csv'),
        os.path.join(script_dir, 'Remittance Advice Remark Codes(RARC) - Sheet1.csv'),
    ]
    for path in rarc_paths:
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
                    rarc_map[code] = desc
                break
            except Exception as e:
                st.warning(f"Error loading RARC: {e}")
    
    return carc_map, rarc_map

# Load recoverability matrix
@st.cache_data
def load_recoverability_matrix():
    """Load recoverability classifications"""
    try:
        from recoverability_matrix import load_full_recoverability_matrix
        recoverability_dict = load_full_recoverability_matrix()
        default_status = {"status": "REVIEW_REQUIRED", "category": "Unknown", "fixable": None, "action": "Review required"}
        return recoverability_dict, default_status
    except Exception as e:
        st.warning(f"Could not load recoverability matrix: {e}")
        return {}, {"status": "REVIEW_REQUIRED", "category": "Unknown", "fixable": None, "action": "Review required"}

# Parse 835 files - EXTRACTS REAL RARC FROM LQ SEGMENTS
def parse_835_files(file_contents_list):
    """Parse uploaded 835 files and extract denial data with REAL RARC codes"""
    import re
    
    denial_records = []
    
    for file_content, filename in file_contents_list:
        try:
            # ALWAYS use regex parser for reliability and LQ extraction
            # The edi_835_parser library doesn't reliably extract LQ segments
            
            # Normalize segment delimiters (handle ~ or newline delimited)
            content = file_content.replace('\n', '~').replace('\r', '')
            segments = [s.strip() for s in content.split('~') if s.strip()]
            
            # Track context for associating RARC with adjustments
            current_claim_id = 'N/A'
            current_patient = 'N/A'
            current_date = 'N/A'
            pending_adjustments = []  # Adjustments waiting for RARC
            
            # First pass: Find all LQ segments (RARC codes) in the file
            # Format: LQ*HE*M143 where M143 is the RARC code
            lq_pattern = r'LQ\*[A-Z]{2}\*([A-Z0-9]+)'
            all_rarcs = re.findall(lq_pattern, file_content)
            rarc_index = 0  # Track which RARC we're on
            
            for i, segment in enumerate(segments):
                fields = segment.split('*')
                seg_id = fields[0] if fields else ''
                
                # CLP = Claim Payment (new claim starts)
                if seg_id == 'CLP' and len(fields) >= 2:
                    current_claim_id = fields[1] if len(fields) > 1 else 'N/A'
                
                # NM1 = Name segment (patient info)
                if seg_id == 'NM1' and len(fields) >= 4:
                    if fields[1] == 'QC':  # QC = Patient
                        current_patient = f"{fields[3]} {fields[4]}" if len(fields) > 4 else fields[3]
                
                # DTM = Date segment
                if seg_id == 'DTM' and len(fields) >= 3:
                    if fields[1] == '232':  # 232 = Service date
                        current_date = fields[2]
                
                # CAS = Claim Adjustment Segment (THE MONEY)
                # Format: CAS*CO*16*125.00*2*50.00~ (group*code*amt*code*amt...)
                if seg_id == 'CAS' and len(fields) >= 4:
                    group_code = fields[1]
                    
                    # CAS can have multiple code/amount pairs
                    j = 2
                    while j + 1 < len(fields):
                        reason_code = fields[j]
                        try:
                            amount = float(fields[j + 1].replace('$', '').replace(',', '') or 0)
                        except:
                            amount = 0.0
                        
                        if reason_code and group_code in ['CO', 'PR', 'OA', 'PI', 'CR']:
                            # FILTER: Skip contractual adjustments - NOT real denials!
                            # CO-45 = Fee schedule discount (expected)
                            # CO-97 = Bundled service (expected)
                            # These are contract terms, NOT billing errors
                            if reason_code in ['45', '97', '59']:
                                j += 3
                                continue
                            
                            # Look for associated RARC in nearby LQ segment
                            rarc_code = ''
                            
                            # Search forward for LQ segment (usually follows CAS)
                            for k in range(i + 1, min(i + 10, len(segments))):
                                lq_seg = segments[k].split('*')
                                if lq_seg[0] == 'LQ' and len(lq_seg) >= 3:
                                    rarc_code = lq_seg[2]
                                    break
                                # Stop if we hit another CAS or CLP
                                if lq_seg[0] in ['CAS', 'CLP', 'SE']:
                                    break
                            
                            denial_records.append({
                                'filename': filename,
                                'patient': current_patient[:50],
                                'claim_id': current_claim_id,
                                'service_date': current_date,
                                'group_code': group_code,
                                'reason_code': reason_code,
                                'code_display': f"{group_code}-{reason_code}",
                                'amount': abs(amount),
                                'charge': 0.0,
                                'rarc': rarc_code,  # REAL RARC from LQ segment!
                            })
                        
                        j += 3  # Skip quantity field, move to next pair
            
            if denial_records:
                # Count how many have real RARC codes
                with_rarc = sum(1 for r in denial_records if r.get('rarc'))
                st.success(f"✓ Parsed {len([r for r in denial_records if r['filename']==filename])} adjustments from {filename} ({with_rarc} with RARC codes)")
            else:
                st.warning(f"⚠️ No CAS segments found in {filename}")
                    
        except Exception as e:
            st.warning(f"Error parsing {filename}: {str(e)}")
    
    return pd.DataFrame(denial_records)

# Parse CSV files from clinics
def parse_csv_files(file_contents_list):
    """Parse uploaded CSV files - handles various column formats from different EHRs"""
    
    all_records = []
    
    for file_content, filename in file_contents_list:
        try:
            import io
            df = pd.read_csv(io.StringIO(file_content))
            
            # Smart column mapping - look for common column names
            col_mapping = {}
            for col in df.columns:
                col_lower = col.lower().strip()
                
                # Map to standard columns
                if any(x in col_lower for x in ['carc', 'reason_code', 'reason code', 'denial_code', 'denial code', 'code']):
                    if 'group' not in col_lower:
                        col_mapping['reason_code'] = col
                elif any(x in col_lower for x in ['group', 'grp', 'adjustment_group']):
                    col_mapping['group_code'] = col
                elif any(x in col_lower for x in ['amount', 'denied', 'denial_amount', 'adj_amt', 'adjustment']):
                    col_mapping['amount'] = col
                elif any(x in col_lower for x in ['patient', 'member', 'subscriber', 'name']):
                    col_mapping['patient'] = col
                elif any(x in col_lower for x in ['claim', 'claim_id', 'claim_number', 'icn']):
                    col_mapping['claim_id'] = col
                elif any(x in col_lower for x in ['date', 'service_date', 'dos']):
                    col_mapping['service_date'] = col
                elif any(x in col_lower for x in ['rarc', 'remark']):
                    col_mapping['rarc'] = col
            
            # Check if we have minimum required columns
            if 'reason_code' not in col_mapping or 'amount' not in col_mapping:
                st.warning(f"⚠️ {filename}: Could not find required columns (reason_code, amount). Found: {list(df.columns)}")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                reason_code = str(row[col_mapping['reason_code']]).strip()
                
                # Extract numeric code if it contains group prefix
                if '-' in reason_code:
                    parts = reason_code.split('-')
                    group_code = parts[0]
                    reason_code = parts[1] if len(parts) > 1 else parts[0]
                else:
                    group_code = row.get(col_mapping.get('group_code', ''), 'CO')
                
                # Clean reason code
                reason_code = ''.join(filter(str.isdigit, str(reason_code)))
                if not reason_code:
                    continue
                
                amount = row[col_mapping['amount']]
                if pd.isna(amount):
                    amount = 0
                else:
                    # Handle currency formatting
                    amount = float(str(amount).replace('$', '').replace(',', '').strip() or 0)
                
                record = {
                    'filename': filename,
                    'patient': str(row.get(col_mapping.get('patient', ''), 'N/A'))[:50],
                    'claim_id': str(row.get(col_mapping.get('claim_id', ''), 'N/A')),
                    'service_date': str(row.get(col_mapping.get('service_date', ''), 'N/A')),
                    'group_code': str(group_code)[:2],
                    'reason_code': reason_code,
                    'code_display': f"{group_code}-{reason_code}",
                    'amount': abs(amount),  # Ensure positive
                    'charge': 0.0,
                    'rarc': str(row.get(col_mapping.get('rarc', ''), '')),
                }
                all_records.append(record)
            
            st.success(f"✓ Parsed {len(df)} rows from {filename}")
            
        except Exception as e:
            st.warning(f"Error parsing {filename}: {str(e)}")
    
    return pd.DataFrame(all_records)

# Main app
def main():
    # ==================== AUTHENTICATION ====================
    if not check_password():
        st.stop()  # Don't continue if not logged in
    
    # ==================== MAIN APPLICATION ====================

    # Load dictionaries
    carc_map, rarc_map = load_code_dictionaries()
    recoverability, default_status = load_recoverability_matrix()

    # Initialize AI training database
    if DATABASE_ENABLED:
        try:
            init_database()
            training_records = get_training_dataset_size()
        except Exception as e:
            st.error(f"Database error: {e}")
            training_records = 0
    else:
        training_records = 0

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #00d4aa; margin: 0;">🔐 VELDEN VAULT</h2>
            <p style="color: #8892a0; font-size: 0.8rem;">Denial Anatomy Audit Tool</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Audit Dashboard", "🔍 Code Lookup", "📄 Generate Report", "🤖 AI Training Data"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # AI Training Data Indicator
        if DATABASE_ENABLED and training_records > 0:
            st.success(f"🤖 **AI Training:** {training_records:,} claims collected")
        
        st.markdown(f"""
        <div style="text-align: center; color: #8892a0; font-size: 0.75rem;">
            <p>Powered by</p>
            <p style="color: #00d4aa; font-weight: 600;">Velden Health</p>
            <p>veldenhealth.com</p>
            <hr style="border-color: #2d3a52; margin: 1rem 0;">
            <p><strong style="color: #00d4aa;">{len(carc_map)}</strong> CARC codes loaded</p>
            <p><strong style="color: #00d4aa;">{len(rarc_map)}</strong> RARC codes loaded</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== CODE LOOKUP PAGE ====================
    if page == "🔍 Code Lookup":
        st.markdown("""
        <div class="main-header">
            <h1>🔍 CARC/RARC Code Lookup</h1>
            <p>Enter a denial code to see its description and recoverability status</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### CARC Code Lookup")
            st.markdown("*Claim Adjustment Reason Codes*")
            
            carc_input = st.text_input(
                "Enter CARC Code",
                placeholder="e.g., 16, 29, 197",
                key="carc_lookup"
            )
            
            if carc_input:
                code = carc_input.strip().upper()
                if code in carc_map:
                    description = carc_map[code]
                    rec_info = recoverability.get(code, default_status)
                    
                    st.success(f"**Code {code} Found**")
                    st.markdown(f"**Description:** {description}")
                    
                    # Professional recoverability status
                    status = rec_info.get('status', 'UNKNOWN')
                    if status == 'VELDEN_FIXABLE':
                        st.markdown('<span class="badge-fixable">✓ Recoverable (Priority)</span>', unsafe_allow_html=True)
                    elif status == 'RESCUE_CANDIDATE':
                        st.markdown('<span class="badge-review">⚡ Rescue Candidate (HFS 1624)</span>', unsafe_allow_html=True)
                    elif status == 'UNRECOVERABLE':
                        st.markdown('<span class="badge-unrecoverable">✗ Process Failure</span>', unsafe_allow_html=True)
                    elif status == 'PARTIALLY_RECOVERABLE':
                        st.markdown('<span class="badge-review">◐ Conditionally Recoverable</span>', unsafe_allow_html=True)
                    elif status == 'PATIENT_RESPONSIBILITY':
                        st.info("💰 Patient Balance")
                    elif status == 'CONTRACTUAL':
                        st.info("📋 Contractual Write-off")
                    
                    # Show action, not just description
                    if rec_info.get('action'):
                        st.markdown(f"**Recovery Action:** {rec_info['action']}")
                else:
                    st.warning(f"Code '{code}' not found in CARC dictionary")
                    # Show suggestions
                    matches = [c for c in carc_map.keys() if code in c][:5]
                    if matches:
                        st.markdown("**Similar codes:** " + ", ".join(matches))
        
        with col2:
            st.markdown("### RARC Code Lookup")
            st.markdown("*Remittance Advice Remark Codes*")
            
            rarc_input = st.text_input(
                "Enter RARC Code",
                placeholder="e.g., M1, N4, MA130",
                key="rarc_lookup"
            )
            
            if rarc_input:
                code = rarc_input.strip().upper()
                if code in rarc_map:
                    description = rarc_map[code]
                    st.success(f"**Code {code} Found**")
                    st.markdown(f"**Description:** {description}")
                else:
                    st.warning(f"Code '{code}' not found in RARC dictionary")
                    matches = [c for c in rarc_map.keys() if code in c][:5]
                    if matches:
                        st.markdown("**Similar codes:** " + ", ".join(matches))
        
        st.divider()
        
        # Quick reference table
        st.markdown("### 📋 Common Denial Codes Quick Reference")
        
        common_codes = [
            ("16", "CO", "Claim lacks information or billing error", "✓ Recoverable (Priority)"),
            ("4", "CO", "Procedure code inconsistent with modifier", "✓ Recoverable (Priority)"),
            ("8", "CO", "Procedure inconsistent with taxonomy", "✓ Recoverable (Priority)"),
            ("29", "CO", "Timely filing - RESCUE with HFS 1624", "⚡ Rescue Candidate"),
            ("197", "CO", "Pre-cert absent - Retro auth possible", "⚡ Rescue Candidate"),
            ("45", "CO", "Charge exceeds fee schedule", "📋 Contractual"),
            ("1", "PR", "Deductible Amount", "💰 Patient Balance"),
            ("2", "PR", "Coinsurance Amount", "💰 Patient Balance"),
        ]
        
        ref_df = pd.DataFrame(common_codes, columns=["Code", "Group", "Description", "Status"])
        st.dataframe(ref_df, use_container_width=True, hide_index=True)
    
    # ==================== AUDIT DASHBOARD PAGE ====================
    elif page == "📊 Audit Dashboard":
        st.markdown("""
        <div class="main-header">
            <h1>📊 Denial Anatomy Audit</h1>
            <p>Upload 835 ERA files <strong>or</strong> CSV denial exports to analyze patterns and identify recoverable revenue</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File upload section - accepts 835, CSV, and DAT files
        uploaded_files = st.file_uploader(
            "Upload Denial Data (835, DAT, or CSV)",
            type=['835', 'txt', 'edi', 'dat', 'csv'],
            accept_multiple_files=True,
            help="Upload 835/DAT ERA files OR CSV exports from your EHR"
        )
        
        if uploaded_files:
            # Separate files by type
            era_files = []
            csv_files = []
            
            for f in uploaded_files:
                content = f.read().decode('utf-8', errors='ignore')
                if f.name.lower().endswith('.csv'):
                    csv_files.append((content, f.name))
                else:
                    era_files.append((content, f.name))
            
            df = pd.DataFrame()
            
            # Parse 835 files
            if era_files:
                with st.spinner(f"Parsing {len(era_files)} ERA file(s)..."):
                    df_era = parse_835_files(era_files)
                    df = pd.concat([df, df_era], ignore_index=True)
            
            # Parse CSV files
            if csv_files:
                with st.spinner(f"Parsing {len(csv_files)} CSV file(s)..."):
                    df_csv = parse_csv_files(csv_files)
                    df = pd.concat([df, df_csv], ignore_index=True)
            
            if len(df) > 0:
                # Enrich with descriptions and recoverability
                df['description'] = df['reason_code'].apply(
                    lambda x: carc_map.get(str(x), 'Unknown')[:80]
                )
                df['recoverability'] = df['reason_code'].apply(
                    lambda x: recoverability.get(str(x), default_status).get('status', 'REVIEW_REQUIRED')
                )
                # Get action from recoverability matrix
                df['action'] = df['reason_code'].apply(
                    lambda x: recoverability.get(str(x), default_status).get('action', 'Review required')
                )
                
                # RARC Integration: Use REAL RARC codes from LQ segments in file
                # NO MORE GUESSING - only show what's actually in the file
                def build_full_description(row):
                    """Build description with REAL RARC from file, not static mapping"""
                    carc_desc = row['description']
                    
                    # Get RARC from parsed file (was extracted from LQ segment)
                    rarc_code = row.get('rarc', '')
                    
                    if rarc_code and rarc_code != '':
                        # Look up RARC description from our reference CSV
                        rarc_desc = rarc_map.get(str(rarc_code), 'Unknown Remark')
                        return f"{carc_desc} [{rarc_code}: {rarc_desc}]"
                    else:
                        # No RARC in file - be honest about it
                        return carc_desc
                
                # Ensure rarc column exists (may not for CSV uploads)
                if 'rarc' not in df.columns:
                    df['rarc'] = ''
                
                df['full_description'] = df.apply(build_full_description, axis=1)
                
                # Save to AI training database (HIPAA-safe - no PHI)
                if DATABASE_ENABLED:
                    try:
                        result = save_ai_training_data(df)
                        if isinstance(result, tuple):
                            records_saved, duplicates = result
                        else:
                            records_saved = result
                            duplicates = 0
                        
                        if records_saved > 0:
                            st.success(f"🤖 Saved {records_saved} new de-identified claims to AI training database")
                        if duplicates > 0:
                            st.info(f"ℹ️ Skipped {duplicates} duplicate claims (already in database)")
                    except Exception as e:
                        st.warning(f"Could not save to AI database: {e}")
                
                # Professional display labels - includes FATAL_PREVENTION
                status_labels = {
                    'VELDEN_FIXABLE': '✓ Recoverable (Priority)',
                    'RESCUE_CANDIDATE': '⚡ Rescue Candidate (HFS 1624)',
                    'FATAL_PREVENTION': '☠️ Fatal (Prevention Required)',
                    'PARTIALLY_RECOVERABLE': '◐ Conditionally Recoverable',
                    'UNRECOVERABLE': '✗ Process Failure',
                    'PATIENT_RESPONSIBILITY': '💰 Patient Balance',
                    'CONTRACTUAL': '📋 Contractual',
                    'REVIEW_REQUIRED': '🔍 Review Required',
                }
                df['status_label'] = df['recoverability'].map(status_labels).fillna(df['recoverability'])
                
                # Calculate metrics - ONLY CO-29 RESCUE is recoverable, NOT CO-197!
                total_denied = df['amount'].sum()
                fixable_amount = df[df['recoverability'] == 'VELDEN_FIXABLE']['amount'].sum()
                rescue_amount = df[df['recoverability'] == 'RESCUE_CANDIDATE']['amount'].sum()
                fatal_amount = df[df['recoverability'] == 'FATAL_PREVENTION']['amount'].sum()
                total_recoverable = fixable_amount + rescue_amount  # ONLY these two!
                unrecoverable = df[df['recoverability'] == 'UNRECOVERABLE']['amount'].sum()
                claim_count = len(df)
                
                # HERO METRICS - Recoverable is the star
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0a0f1a 0%, #1a2744 100%); 
                            padding: 2rem; border-radius: 16px; text-align: center; 
                            border: 2px solid #00d4aa; margin-bottom: 2rem;">
                    <p style="color: #8892a0; margin: 0; font-size: 1rem; text-transform: uppercase; letter-spacing: 2px;">
                        Total Recoverable Revenue
                    </p>
                    <h1 style="color: #00d4aa; font-size: 4rem; margin: 0.5rem 0; font-weight: 800;">
                        ${total_recoverable:,.2f}
                    </h1>
                    <p style="color: #00d4aa; font-size: 1.2rem;">
                        {(total_recoverable/total_denied*100):.1f}% of denied claims can be recovered
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Secondary metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Denied", f"${total_denied:,.2f}")
                with col2:
                    st.metric("Priority Recovery", f"${fixable_amount:,.2f}")
                with col3:
                    st.metric("Rescue Candidates", f"${rescue_amount:,.2f}")
                with col4:
                    st.metric("Claims Analyzed", f"{claim_count:,}")
                
                st.divider()
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Top Denial Reasons by Revenue Impact")
                    top_denials = df.groupby(['code_display', 'description'])['amount'].sum().reset_index()
                    top_denials = top_denials.nlargest(10, 'amount')
                    
                    fig = px.bar(
                        top_denials, 
                        x='amount', 
                        y='code_display',
                        orientation='h',
                        color='amount',
                        color_continuous_scale=['#1a2744', '#00d4aa'],
                        labels={'amount': 'Amount ($)', 'code_display': 'Denial Code'}
                    )
                    fig.update_layout(
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#e0e6ed',
                        yaxis=dict(autorange="reversed")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("### Recoverability Breakdown")
                    rec_summary = df.groupby('status_label')['amount'].sum().reset_index()
                    
                    colors = {
                        '✓ Recoverable (Priority)': '#00d4aa',
                        '⚡ Rescue Candidate (HFS 1624)': '#f39c12',
                        '☠️ Fatal (Prevention Required)': '#c0392b',
                        '◐ Conditionally Recoverable': '#3498db',
                        '✗ Process Failure': '#e74c3c',
                        '💰 Patient Balance': '#9b59b6',
                        '📋 Contractual': '#95a5a6',
                        '🔍 Review Required': '#f1c40f',
                    }
                    
                    fig = px.pie(
                        rec_summary,
                        values='amount',
                        names='status_label',
                        color='status_label',
                        color_discrete_map=colors,
                        hole=0.4
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#e0e6ed'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed table with RARC-enriched descriptions and actions
                st.markdown("### 📋 Detailed Denial Records")
                st.dataframe(
                    df[['code_display', 'full_description', 'amount', 'status_label', 'action']].head(100),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'code_display': 'Code',
                        'full_description': 'Description [RARC]',
                        'amount': st.column_config.NumberColumn('Amount', format="$%.2f"),
                        'status_label': 'Status',
                        'action': 'Recommended Action'
                    }
                )
                
                # Export buttons
                col1, col2 = st.columns(2)
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV Report",
                        csv,
                        "velden_denial_audit.csv",
                        "text/csv"
                    )
                with col2:
                    st.session_state['audit_data'] = df
                    st.info("💡 Go to 'Generate Report' to create a branded HTML report")
            else:
                st.warning("No denial data found in the uploaded files.")
        else:
            # Demo mode
            st.info("👆 Upload 835 ERA files to begin analysis, or run `python mock_835_generator.py` to create test data.")
    
    # ==================== GENERATE REPORT PAGE ====================
    elif page == "📄 Generate Report":
        st.markdown("""
        <div class="main-header">
            <h1>📄 Generate Forensic Report</h1>
            <p>Create a branded revenue recovery report for your client</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'audit_data' in st.session_state and len(st.session_state['audit_data']) > 0:
            df = st.session_state['audit_data']
            
            st.success(f"✓ Audit data loaded: {len(df)} denial records")
            
            # Report options
            col1, col2 = st.columns(2)
            with col1:
                client_name = st.text_input("Client/Clinic Name", "Sample Behavioral Health Clinic")
            with col2:
                report_date = st.date_input("Report Date", datetime.now())
            
            if st.button("🚀 Generate HTML Report", type="primary"):
                # Calculate summary stats with RESCUE included
                total = df['amount'].sum()
                fixable = df[df['recoverability'] == 'VELDEN_FIXABLE']['amount'].sum()
                rescue = df[df['recoverability'] == 'RESCUE_CANDIDATE']['amount'].sum()
                total_recoverable = fixable + rescue
                unrecoverable = df[df['recoverability'] == 'UNRECOVERABLE']['amount'].sum()
                
                # Professional status labels for display
                status_display = {
                    'VELDEN_FIXABLE': '✓ Recoverable (Priority)',
                    'RESCUE_CANDIDATE': '⚡ Rescue (HFS 1624)',
                    'FATAL_PREVENTION': '☠️ Fatal (Prevention)',
                    'PARTIALLY_RECOVERABLE': '◐ Conditionally Recoverable',
                    'UNRECOVERABLE': '✗ Process Failure',
                    'PATIENT_RESPONSIBILITY': '💰 Patient Balance',
                    'CONTRACTUAL': '📋 Contractual',
                    'REVIEW_REQUIRED': '🔍 Review Required',
                }
                
                # Build table HTML BEFORE the template (NO truncation!)
                report_df = df.groupby(['code_display', 'recoverability']).agg({
                    'amount': 'sum',
                    'full_description': 'first',
                    'action': 'first'
                }).reset_index().nlargest(10, 'amount')
                
                table_rows_html = ""
                for _, row in report_df.iterrows():
                    status = row['recoverability']
                    if status == 'VELDEN_FIXABLE':
                        css_class = 'status-recoverable'
                    elif status == 'RESCUE_CANDIDATE':
                        css_class = 'status-rescue'
                    elif status == 'FATAL_PREVENTION':
                        css_class = 'status-fatal'
                    elif status == 'UNRECOVERABLE':
                        css_class = 'status-failure'
                    elif status == 'PATIENT_RESPONSIBILITY':
                        css_class = 'status-patient'
                    else:
                        css_class = 'status-contractual'
                    
                    status_text = status_display.get(status, status)
                    table_rows_html += f'''<tr>
                        <td><strong>{row['code_display']}</strong></td>
                        <td>{row['full_description']}</td>
                        <td><strong>${row['amount']:,.2f}</strong></td>
                        <td class="{css_class}">{status_text}</td>
                        <td>{row['action']}</td>
                    </tr>'''
                
                # Embed logo as base64 for standalone HTML
                logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'velden_logo.png')
                logo_b64 = ""
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        logo_b64 = base64.b64encode(f.read()).decode('utf-8')
                
                # Generate HTML report with HERO number and logo
                html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Velden Health - Forensic Revenue Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            background-color: #ffffff;
            color: #333333;
            min-height: 100vh;
            padding: 40px;
            line-height: 1.5;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 3px solid #003366;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #003366;
            font-size: 1.8rem;
            margin-bottom: 5px;
            font-weight: 700;
        }}
        .header .subtitle {{ color: #666666; font-size: 0.9rem; }}
        .header .client {{ 
            color: #003366; 
            font-size: 1.4rem; 
            margin-top: 15px;
            font-weight: 700;
        }}
        
        /* HERO SECTION - Clean Professional */
        .hero {{
            background-color: #f8f9fa;
            border: 2px solid #003366;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .hero-label {{
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }}
        .hero-value {{
            color: #2E7D32;
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1;
        }}
        .hero-subtext {{
            color: #388E3C;
            font-size: 1.1rem;
            margin-top: 12px;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        .metric-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #003366;
        }}
        .metric-label {{
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.7rem;
            margin-top: 8px;
        }}
        
        .section {{
            background-color: #ffffff;
            border-radius: 6px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #dee2e6;
        }}
        .section h2 {{
            color: #003366;
            margin-bottom: 15px;
            font-size: 1.1rem;
            border-bottom: 2px solid #003366;
            padding-bottom: 8px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{ 
            color: #003366; 
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            background-color: #f8f9fa;
            font-weight: 700;
        }}
        td {{ font-size: 0.85rem; color: #333333; }}
        
        .status-recoverable {{ color: #2E7D32; font-weight: 700; }}
        .status-rescue {{ color: #E65100; font-weight: 700; }}
        .status-fatal {{ color: #C62828; font-weight: 700; }}
        .status-failure {{ color: #D32F2F; font-weight: 700; }}
        .status-patient {{ color: #7B1FA2; font-weight: 700; }}
        .status-contractual {{ color: #616161; font-weight: 700; }}
        
        .cta {{
            background-color: #003366;
            color: #ffffff;
            padding: 35px;
            border-radius: 8px;
            text-align: center;
            margin-top: 30px;
        }}
        .cta h2 {{ 
            color: #ffffff; 
            font-size: 1.4rem;
            margin-bottom: 8px; 
        }}
        .cta p {{ font-size: 1rem; margin-bottom: 15px; color: #e0e0e0; }}
        .cta a {{
            display: inline-block;
            background: #ffffff;
            color: #003366;
            padding: 14px 40px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 700;
            font-size: 1rem;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666666;
            font-size: 0.8rem;
            border-top: 1px solid #dee2e6;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="data:image/png;base64,{logo_b64}" alt="Velden Health" style="height: 60px; margin-bottom: 20px;" />
            <p style="font-size: 1.3rem; color: #333; margin-bottom: 5px;">Forensic Revenue Recovery Report</p>
            <p class="client">{client_name}</p>
            <p class="subtitle">Generated: {report_date.strftime('%B %d, %Y')}</p>
        </div>
        
        <!-- HERO SECTION - This is what sells -->
        <div class="hero">
            <p class="hero-label">Total Recoverable Revenue</p>
            <p class="hero-value">${total_recoverable:,.2f}</p>
            <p class="hero-subtext">{(total_recoverable/total*100):.1f}% of denied revenue can be recovered</p>
        </div>
        
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-value" style="color: #003366;">${total:,.2f}</div>
                <div class="metric-label">Total Denied</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #E65100;">${rescue:,.2f}</div>
                <div class="metric-label">Rescue Candidates (HFS 1624)</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #003366;">{len(df)}</div>
                <div class="metric-label">Claims Analyzed</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Top Denial Reasons by Revenue Impact</h2>
            <table>
                <tr>
                    <th>Code</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
                {table_rows_html}
            </table>
        </div>
        
        <div class="cta">
            <h2>Ready to Recover ${total_recoverable:,.2f}?</h2>
            <p>Our team specializes in exactly these types of denials. Let's get your money back.</p>
            <a href="https://www.veldenhealth.com/contact.html">Schedule Free Recovery Consultation →</a>
        </div>
        
        <div class="footer">
            <p><strong>Velden Health</strong> | Illinois Behavioral Health A/R Recovery Specialist</p>
            <p>veldenhealth.com | (312) 555-0123</p>
        </div>
    </div>
</body>
</html>
"""
                st.download_button(
                    "📥 Download HTML Report",
                    html_report,
                    f"Velden_Forensic_Report_{client_name.replace(' ', '_')}.html",
                    "text/html"
                )
                
                st.markdown("### Report Preview")
                st.components.v1.html(html_report, height=800, scrolling=True)
        else:
            st.warning("⚠️ No audit data available. Please upload and analyze 835 files first in the Audit Dashboard.")
    
    # ==================== AI TRAINING DATA PAGE ====================
    elif page == "🤖 AI Training Data":
        st.markdown("""
        <div class="main-header">
            <h1>🤖 AI Training Data</h1>
            <p>View and download de-identified claims data collected for future AI risk scoring</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not DATABASE_ENABLED:
            st.error("Database module not loaded. AI training data collection is disabled.")
        elif training_records == 0:
            st.info("📊 No training data collected yet. Upload denial data in the Audit Dashboard to start collecting.")
        else:
            st.success(f"✅ **{training_records:,} claims** stored in AI training database")
            
            # Display data
            try:
                import sqlite3
                conn = sqlite3.connect('ai_training_data.db')
                
                # Get all data
                df_training = pd.read_sql('SELECT * FROM payer_performance ORDER BY upload_date DESC LIMIT 1000', conn)
                conn.close()
                
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    unique_payers = df_training['payer_name'].nunique()
                    st.metric("Unique Payers", unique_payers)
                with col2:
                    unique_codes = df_training['denial_code'].nunique()
                    st.metric("Denial Code Types", unique_codes)
                with col3:
                    total_amount = df_training['adjustment_amount'].sum()
                    st.metric("Total Denied", f"${total_amount:,.2f}")
                with col4:
                    recent_upload = df_training['upload_date'].max()
                    if recent_upload and not pd.isna(recent_upload):
                        upload_date_str = str(recent_upload)[:10]
                    else:
                        upload_date_str = "N/A"
                    st.metric("Last Upload", upload_date_str)
                
                st.divider()
                
                # Display table
                st.markdown("### 📋 Recent Claims Data (HIPAA-Safe)")
                st.caption("🔒 All patient identifiers have been removed or hashed")
                
                # Select columns to display
                display_cols = ['upload_date', 'payer_name', 'denial_code', 'recoverability_status', 
                               'adjustment_amount', 'rarc_code', 'state']
                st.dataframe(
                    df_training[display_cols].head(100),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download options
                st.divider()
                st.markdown("### 📥 Export Data")
                
                col1, col2 = st.columns(2)
                with col1:
                    # CSV export
                    csv_data = df_training.to_csv(index=False)
                    st.download_button(
                        "📄 Download as CSV",
                        csv_data,
                        "ai_training_data.csv",
                        "text/csv"
                    )
                
                with col2:
                    # SQLite database export
                    with open('ai_training_data.db', 'rb') as f:
                        db_bytes = f.read()
                    st.download_button(
                        "💾 Download SQLite Database",
                        db_bytes,
                        "ai_training_data.db",
                        "application/octet-stream"
                    )
                
                # Data insights
                st.divider()
                st.markdown("### 📊 Quick Insights")
                
                # Top payers by denial amount
                top_payers = df_training.groupby('payer_name')['adjustment_amount'].sum().sort_values(ascending=False).head(5)
                if len(top_payers) > 0:
                    st.markdown("**Top 5 Payers by Denial Amount:**")
                    for payer, amount in top_payers.items():
                        st.write(f"- {payer}: ${amount:,.2f}")
                
            except Exception as e:
                st.error(f"Error loading training data: {e}")

if __name__ == "__main__":
    main()

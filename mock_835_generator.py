# Velden Vault - Mock 835 Data Generator
# Creates realistic 835 ERA test files for development

import os
import random
from datetime import datetime, timedelta

# Payer configurations
PAYERS = [
    {"name": "BLUE CROSS BLUE SHIELD OF IL", "id": "00621"},
    {"name": "AETNA BETTER HEALTH IL", "id": "60054"},
    {"name": "UNITED HEALTHCARE", "id": "87726"},
    {"name": "CIGNA HEALTHCARE", "id": "62308"},
    {"name": "HUMANA", "id": "61101"},
]

# Provider configurations (therapists)
PROVIDERS = [
    {"name": "JOHNSON SARAH A", "npi": "1234567890", "specialty": "LCPC"},
    {"name": "WILLIAMS MICHAEL R", "npi": "2345678901", "specialty": "LCSW"},
    {"name": "BROWN JENNIFER L", "npi": "3456789012", "specialty": "PhD"},
    {"name": "DAVIS ROBERT K", "npi": "4567890123", "specialty": "LCPC"},
    {"name": "MILLER AMANDA J", "npi": "5678901234", "specialty": "LMFT"},
]

# Denial scenarios with weights (more common denials appear more often)
DENIAL_SCENARIOS = [
    {"carc": "16", "group": "CO", "desc": "Missing modifier/taxonomy", "amount_range": (80, 250), "weight": 25},
    {"carc": "4", "group": "CO", "desc": "Modifier error", "amount_range": (100, 200), "weight": 15},
    {"carc": "8", "group": "CO", "desc": "Taxonomy mismatch", "amount_range": (120, 280), "weight": 15},
    {"carc": "29", "group": "CO", "desc": "Timely filing", "amount_range": (150, 350), "weight": 10},
    {"carc": "197", "group": "CO", "desc": "Pre-cert missing", "amount_range": (200, 500), "weight": 10},
    {"carc": "96", "group": "CO", "desc": "Non-covered charge", "amount_range": (100, 300), "weight": 8},
    {"carc": "50", "group": "CO", "desc": "Medical necessity", "amount_range": (150, 400), "weight": 5},
    {"carc": "182", "group": "CO", "desc": "Invalid modifier", "amount_range": (80, 180), "weight": 5},
    {"carc": "206", "group": "CO", "desc": "NPI missing", "amount_range": (100, 250), "weight": 3},
    {"carc": "27", "group": "CO", "desc": "Coverage terminated", "amount_range": (120, 300), "weight": 2},
    {"carc": "1", "group": "PR", "desc": "Deductible", "amount_range": (50, 200), "weight": 2},
]

# Patient name generator
FIRST_NAMES = ["JAMES", "MARY", "JOHN", "PATRICIA", "ROBERT", "JENNIFER", "MICHAEL", "LINDA", "DAVID", "ELIZABETH"]
LAST_NAMES = ["SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA", "MILLER", "DAVIS", "RODRIGUEZ", "MARTINEZ"]

def generate_patient_name():
    return f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)}"

def generate_claim_id():
    return f"CLM{random.randint(100000000, 999999999)}"

def weighted_random_choice(scenarios):
    total_weight = sum(s['weight'] for s in scenarios)
    r = random.uniform(0, total_weight)
    cumulative = 0
    for scenario in scenarios:
        cumulative += scenario['weight']
        if r <= cumulative:
            return scenario
    return scenarios[-1]

def generate_835_content(payer, claims_count=20):
    """Generate an 835 EDI file content"""
    lines = []
    
    # ISA header
    now = datetime.now()
    date_str = now.strftime("%y%m%d")
    time_str = now.strftime("%H%M")
    isa_control = str(random.randint(100000000, 999999999))
    
    lines.append(f"ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *{date_str}*{time_str}*^*00501*{isa_control}*0*P*:~")
    lines.append(f"GS*HP*SENDER*RECEIVER*{now.strftime('%Y%m%d')}*{time_str}*1*X*005010X221A1~")
    lines.append("ST*835*0001~")
    lines.append(f"BPR*I*0*C*NON************{now.strftime('%Y%m%d')}~")
    lines.append(f"TRN*1*{random.randint(10000000, 99999999)}*1{payer['id']}~")
    lines.append(f"DTM*405*{now.strftime('%Y%m%d')}~")
    
    # Payer info (N1 Loop 1000A)
    lines.append(f"N1*PR*{payer['name']}*XV*{payer['id']}~")
    lines.append("N3*PO BOX 12345~")
    lines.append("N4*CHICAGO*IL*606010000~")
    
    # Payee info (N1 Loop 1000B)
    lines.append("N1*PE*VELDEN HEALTH PARTNERS*XX*1122334455~")
    lines.append("N3*123 HEALTHCARE BLVD~")
    lines.append("N4*CHICAGO*IL*606011234~")
    
    # Generate claims
    for i in range(claims_count):
        provider = random.choice(PROVIDERS)
        scenario = weighted_random_choice(DENIAL_SCENARIOS)
        patient = generate_patient_name()
        claim_id = generate_claim_id()
        service_date = (now - timedelta(days=random.randint(30, 180))).strftime("%Y%m%d")
        charge_amount = round(random.uniform(*scenario['amount_range']), 2)
        
        # CLP segment (Claim Payment)
        # CLP01=Claim ID, CLP02=Status (4=Denied), CLP03=Charge, CLP04=Paid, CLP05=Patient Resp
        lines.append(f"CLP*{claim_id}*4*{charge_amount}*0*0*MC*{random.randint(1000000, 9999999)}~")
        
        # NM1 segment for patient
        lines.append(f"NM1*QC*1*{patient.split()[0]}*{patient.split()[1]}****MI*{random.randint(100000000, 999999999)}~")
        
        # NM1 segment for rendering provider
        name_parts = provider['name'].split()
        lines.append(f"NM1*82*1*{name_parts[0]}*{name_parts[1]}*{name_parts[2] if len(name_parts) > 2 else ''}***XX*{provider['npi']}~")
        
        # DTM for service date
        lines.append(f"DTM*232*{service_date}~")
        
        # SVC segment (Service Payment)
        lines.append(f"SVC*HC:90837*{charge_amount}*0**1~")
        lines.append(f"DTM*472*{service_date}~")
        
        # CAS segment (Claim Adjustment)
        lines.append(f"CAS*{scenario['group']}*{scenario['carc']}*{charge_amount}~")
    
    # Footer segments
    lines.append("SE*" + str(len(lines) - 2) + "*0001~")
    lines.append("GE*1*1~")
    lines.append("IEA*1*" + isa_control + "~")
    
    return "\n".join(lines)

def create_mock_files(output_dir="client_data", num_files=5, claims_per_file=20):
    """Create multiple mock 835 files"""
    os.makedirs(output_dir, exist_ok=True)
    
    files_created = []
    for i in range(num_files):
        payer = random.choice(PAYERS)
        content = generate_835_content(payer, claims_per_file)
        
        filename = f"ERA_{payer['name'].replace(' ', '_')[:15]}_{datetime.now().strftime('%Y%m%d')}_{i+1}.835"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        files_created.append(filepath)
        print(f"✓ Created: {filename}")
    
    return files_created

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  VELDEN VAULT - Mock 835 Generator")
    print("="*50 + "\n")
    
    files = create_mock_files(num_files=5, claims_per_file=25)
    
    print(f"\n✓ Generated {len(files)} mock 835 files in 'client_data/' folder")
    print("  Ready for testing with the audit tool!\n")

# Velden Vault - Deployment Guide

## 🚀 Deploy to Streamlit Cloud (FREE)

### Step 1: Prepare Your Code

1. **Install Git** (if not already installed):
   - Download from https://git-scm.com/

2. **Initialize Repository:**
```bash
cd "d:\Student Assignments\student_protfolios\Medexa_healthCare\Tools\Valden vault"
git init
git add .
git commit -m "Initial commit - Velden Vault with authentication and AI data collection"
```

3. **Create GitHub Repository:**
   - Go to https://github.com/new
   - Name: `velden-vault`
   - Privacy: Private (recommended for healthcare tools)
   - Click "Create repository"

4. **Push to GitHub:**
```bash
git remote add origin https://github.com/YOUR_USERNAME/velden-vault.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy to Streamlit Cloud

1. **Sign Up:**
   - Go to https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App:**
   - Click "New app"
   - Select repository: `velden-vault`
   - Branch: `main`
   - Main file path: `app.py`

3. **Add Secrets (IMPORTANT):**
   - In deployment settings → "Secrets"
   - Paste this:
   ```toml
   [passwords]
   admin_username = "Admin"
   admin_password = "Admin123"
   ```
   - Click "Save"

4. **Deploy:**
   - Click "Deploy!"
   - Wait 2-3 minutes for build

5. **Access Your App:**
   - URL will be: `https://YOUR_APP_NAME.streamlit.app`

---

### Step 3: Test Your Deployment

1. Open the URL
2. Login with:
   - Username: `Admin`
   - Password: `Admin123`
3. Upload a test 835 file
4. Verify AI data collection message appears

---

## 🔒 HIPAA Compliance Notes

**What's Safe:**
- ✅ Tool is deployed (web interface)
- ✅ Login protection (username/password)
- ✅ De-identified data in database (no patient names/IDs)
- ✅ Aggregated payer statistics only

**What's NOT Stored:**
- ❌ Patient names
- ❌ Member IDs
- ❌ Specific service dates
- ❌ Provider NPIs
- ❌ Uploaded 835 files

**Bottom Line:** The deployed version is HIPAA-safe because it stores NO PHI. All sensitive data is hashed or excluded.

---

## 🔐 Security Best Practices

### Change Default Password:
1. In Streamlit Cloud → Your App → Settings → Secrets
2. Update:
```toml
[passwords]
admin_username = "YourUsername"
admin_password = "YourStrongPassword123!"
```

### Enable HTTPS (automatic):
- Streamlit Cloud automatically uses HTTPS
- All data transmission is encrypted

---

## 📊 AI Training Data

The tool automatically collects de-identified data for future AI:
- Payer performance stats
- CPT code approval rates
- Denial reason patterns
- State-level trends

Database file: `ai_training_data.db`

---

## 💰 Cost

**Streamlit Community Cloud:**
- FREE forever
- 1GB storage
- Custom domain available
- Perfect for pilot/demos

**Upgrade Later (when needed):**
- AWS with HIPAA BAA: ~$100/month
- Enterprise Streamlit: Custom pricing

---

## 🆘 Troubleshooting

**Login not working:**
- Check secrets.toml is configured correctly
- Verify no typos in username/password

**Files not uploading:**
- Check file size < 200MB
- Ensure file extension is .835, .dat, .csv, or .edi

**Database errors:**
- Normal on first deploy - database auto-creates on first data save

---

## 📞 Support

For deployment help:
- Streamlit Docs: https://docs.streamlit.io/
- Community Forum: https://discuss.streamlit.io/

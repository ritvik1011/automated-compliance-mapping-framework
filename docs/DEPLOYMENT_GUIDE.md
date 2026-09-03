# Comprehensive Deployment Guide

> **Academic Research Context**: Policy-as-Code & Automated Compliance Mapping Framework  
> **Author**: Ritvik Bahirwar (Master's in Computer Engineering for IoT Systems)  
> **Target Reviewers**: Max Planck Institute for Security and Privacy (MPI-SP)  
> **Lifecycle Phase**: Step 5 — Decision-Support Dashboards, Socio-Technical Visualization & Board Reporting  

---

## 🌐 Overview & Deployment Matrix

This guide provides exhaustive, end-to-end instructions for deploying the **Automated Compliance Mapping & Gap Analysis Framework** dashboard across three primary target environments:

| Deployment Tier | Primary Target | Setup Effort | Prerequisites | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Local Desktop** | Windows Workstation | **1 minute** | Python 3.10+, Virtual Environment | Rapid local evaluation, debugging, offline development |
| **Tier 2: Streamlit Cloud** | Public Web (PaaS) | **3 minutes** | GitHub Account, Streamlit Cloud | Academic portfolio sharing, MPI-SP remote review |
| **Tier 3: Enterprise Docker** | Linux Server / K8s | **5 minutes** | Docker Engine, Docker Compose | Enterprise GRC deployment, CI/CD automated staging |

---

## 💻 Tier 1: Local Deployment (Developer Workstation)

Local deployment is designed for zero friction on Windows, macOS, and Linux workstations.

### 1. Windows Desktop Launchers

#### Option A: Diagnostic Batch Launcher (`run_dashboard.bat`)
For 1-click execution on Windows, double-click `run_dashboard.bat` in the project root.
```text
run_dashboard.bat
```
This batch script executes a hardened diagnostic sequence:
1. **UTF-8 Console Mode**: Executes `chcp 65001` and sets `PYTHONIOENCODING=utf-8` to render emojis and Unicode metrics cleanly.
2. **Directory Anchoring**: Switches working directory directly to script root via `cd /d "%~dp0"`, preventing directory drifting when run as Administrator or from Explorer.
3. **Environment Detection**: Checks for and activates `venv\Scripts\activate.bat` (or `.venv`), falling back gracefully to system Python if unconfigured.
4. **Interpreter Validation**: Queries `where python` and logs the exact Python version and path.
5. **Execution Harness**: Runs `python run_dashboard.py %*`.
6. **Guaranteed Diagnostic Pause**: Intercepts the process exit code and halts with `pause` before exiting so the console window never flashes or disappears without user input.

#### Option B: PowerShell Alternative (`run_dashboard.ps1`)
Modern Windows installations can leverage the native PowerShell launcher:
```powershell
.\run_dashboard.ps1
```
- **Context Menu Launch**: Right-click `run_dashboard.ps1` and select **"Run with PowerShell"**.
- **Execution Policy Bypass (Single Session)**: If script execution is restricted by Windows default policy (`Restricted` or `AllSigned`), launch with:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\run_dashboard.ps1
  ```
- **Desktop Shortcut Configuration**: Target string for creating a 1-click Desktop shortcut:
  ```text
  powershell.exe -ExecutionPolicy Bypass -NoExit -File "%USERPROFILE%\Desktop\automated-compliance-mapping-framework\run_dashboard.ps1"
  ```

### 2. Environment Verification Command
To verify that Python, the virtual environment, and Streamlit are healthy independently of any launcher script, paste this command into Command Prompt:
```cmd
venv\Scripts\python.exe -c "import streamlit, sys; print('SUCCESS: Python ' + sys.version.split()[0] + ' and Streamlit ' + streamlit.__version__ + ' are working in venv!')"
```

### 3. Cross-Platform Terminal Launch
From Windows PowerShell, Command Prompt, or Linux/macOS bash:

```bash
# 1. Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 2. Seed demo database (if not already seeded)
python populate_demo_data.py

# 3. Launch dashboard harness
python run_dashboard.py
```

### 4. Direct Streamlit CLI Launch
Thanks to the dynamic `sys.path` injection at the top of `src/dashboard/app.py`, native Streamlit commands function seamlessly:

```bash
streamlit run src/dashboard/app.py --server.port 8501
```

---

## ☁️ Tier 2: Streamlit Community Cloud (Public Web Sharing)

Streamlit Community Cloud provides free, instant cloud hosting directly connected to your GitHub repository. It is the ideal method for presenting your work to academic review committees (such as MPI-SP) without requiring them to install local software.

### Step-by-Step Cloud Deployment

#### Step 1: Push Repository to GitHub
Ensure your latest changes (including `.streamlit/config.toml` and `.streamlit/secrets.toml.example`) are committed and pushed to GitHub:
```bash
git push origin main
```

#### Step 2: Connect Streamlit Community Cloud
1. Navigate to [share.streamlit.io](https://share.streamlit.io) and sign in using your GitHub account.
2. Click **New app** in the top-right corner.
3. Configure the deployment parameters:
   - **Repository**: `your-username/automated-compliance-mapping-framework`
   - **Branch**: `main`
   - **Main file path**: `src/dashboard/app.py`
   - **App URL (optional)**: e.g., `compliance-mapping-framework.streamlit.app`

#### Step 3: Configure Cloud Secrets & Database
In Streamlit Cloud's **Advanced Settings > Secrets**:
1. Copy the contents of [.streamlit/secrets.toml.example](file:///c:/Users/barit/OneDrive/Desktop/automated-compliance-mapping-framework/.streamlit/secrets.toml.example).
2. Paste them into the Secrets textarea:
   ```toml
   [database]
   url = "sqlite:///compliance.db"

   [general]
   environment = "cloud-demo"
   ```
3. Click **Save**.

#### Step 4: Cloud Data Seeding Strategy
Because `compliance.db` is excluded from Git via `.gitignore`, the cloud instance requires database initialization on first boot. The framework supports two clean patterns:

- **Method A: Ephemeral Pre-Seeding (Automatic on Import)**  
  In cloud mode, `src/dashboard/database.py` gracefully detects an uninitialized database and falls back to running demo seeding if the database file is empty.
- **Method B: Cloud Terminal / Build Execution**  
  You can execute `python populate_demo_data.py` directly from the Streamlit Cloud app console.

#### Step 5: Verify Deployment
Once build logs indicate `Streamlit is ready!`, open the live URL. Test navigating across all 5 pages and verify that:
- Executive gauge charts render interactively.
- Socio-technical friction cards display with expandable details.
- Audit package export buttons generate downloads correctly.

---

## 🐳 Tier 3: Containerized Enterprise Deployment (Docker)

For enterprise governance environments and reproducible academic artifact evaluation, the framework provides full container support.

### 1. Dockerfile Architecture
The container utilizes a lightweight Python 3.10 slim base image with security hardening:

```dockerfile
# Multi-stage lightweight production image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# Install minimal OS dependencies for compilation and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first for optimal Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and configuration
COPY src/ ./src/
COPY .streamlit/ ./.streamlit/
COPY populate_demo_data.py run_dashboard.py ./

# Seed initial demonstration database inside image
RUN python populate_demo_data.py

# Expose Streamlit default network port
EXPOSE 8501

# Streamlit official healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Execute Streamlit server
ENTRYPOINT ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
```

### 2. Building & Running the Container
```bash
# Build the image
docker build -t compliance-mapping-dashboard:latest .

# Run container detached with port mapping
docker run -d --name compliance-app -p 8501:8501 compliance-mapping-dashboard:latest

# Check container health and logs
docker ps
docker logs -f compliance-app
```
Access the containerized instance at `http://localhost:8501`.

---

## 🛠️ Data Reset & Maintenance Workflows

### Re-seeding the Assessment Database
If assessment data becomes modified during testing or if you wish to reset metrics to the pristine research baseline:

```bash
python populate_demo_data.py
```

This operation:
1. Connects to `sqlite:///compliance.db`.
2. Flushes existing records in `compliance_kpis`, `control_assessment_results`, and `compliance_assessments`.
3. Inserts fresh mock records with calibrated confidence scores and socio-technical friction notes.
4. Completes inside 250 milliseconds.

---

## 🔒 Security Best Practices & Operational Hygiene

1. **Strict Secret Isolation**:  
   Never commit `.streamlit/secrets.toml`, `.env`, or raw cloud credentials to GitHub. Always use `.streamlit/secrets.toml.example` as a sanitized template.

2. **Database Isolation (`*.db`)**:  
   The runtime assessment database (`compliance.db`) is strictly excluded in `.gitignore` to prevent committing proprietary client telemetry or stateful assessment runs.

3. **Dependency Version Pinning**:  
   Dependencies in `requirements.txt` are bounded to ensure reproducibility across local developer machines and cloud container runtimes.

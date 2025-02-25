# Fixing "Python not found" Error with Google Cloud SDK on Windows

If you're encountering the "Python was not found" error when trying to use Google Cloud SDK on Windows, follow this guide to resolve the issue.

## The Problem

When running `gcloud` commands in Git Bash (MINGW64) on Windows, you might see errors like:

```
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Manage App Execution Aliases.
```

This happens because:
1. Google Cloud SDK requires Python to run
2. Windows has special handling for Python execution
3. Git Bash (MINGW64) doesn't properly interact with Windows Python execution aliases

## Solution 1: Reinstall Google Cloud SDK with Bundled Python

This is the recommended solution:

1. **Uninstall your current Google Cloud SDK installation**:
   - Go to Windows Settings > Apps > Apps & features
   - Find "Google Cloud SDK" and uninstall it

2. **Download the latest Google Cloud SDK installer**:
   - Visit: https://cloud.google.com/sdk/docs/install-sdk#windows
   - Download the installer (not the ZIP file)

3. **Run the installer and select bundled Python**:
   - During installation, you'll be asked if you want to use the bundled Python
   - Make sure to select **YES** to this option
   - Complete the installation

4. **Open a new PowerShell or Command Prompt window** (not Git Bash):
   - This is important - use PowerShell or Command Prompt for Google Cloud SDK on Windows
   - Git Bash often has issues with Python on Windows

5. **Initialize and authenticate**:
   ```
   gcloud init
   gcloud auth login
   ```

## Solution 2: Configure Google Cloud SDK to Use Your Python Installation

If you prefer to use your existing Python installation:

1. **Open PowerShell or Command Prompt as Administrator**

2. **Find your Python installation path**:
   ```
   where python
   ```
   This will show the full path to your Python executable, like `C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe`

3. **Configure Google Cloud SDK to use this Python**:
   ```
   gcloud config set component_manager/disable_update_check true
   gcloud config set core/disable_usage_reporting true
   gcloud config set component_manager/python "C:\path\to\your\python.exe"
   ```
   Replace `C:\path\to\your\python.exe` with the actual path from step 2

4. **Test if it works**:
   ```
   gcloud --version
   ```

## Solution 3: Use PowerShell Script Instead of Bash Script

We've created a PowerShell script that performs the same setup as the bash script but works better on Windows:

1. **Open PowerShell** (not Git Bash)

2. **Navigate to your project directory**:
   ```
   cd D:\path\to\Resume_answers_agent
   ```

3. **Run the PowerShell setup script**:
   ```
   .\scripts\manual_gcp_setup.ps1
   ```

## Additional Tips

1. **Always use PowerShell or Command Prompt** for Google Cloud SDK on Windows, not Git Bash

2. **If you need to use Git Bash**, you can try:
   ```
   CLOUDSDK_PYTHON=python gcloud command
   ```
   This sets the Python interpreter for that specific command

3. **Check your PATH environment variable** to ensure Python is properly configured

4. **Verify Python works** by running:
   ```
   python --version
   ```
   in both PowerShell and Git Bash to see if there are differences

## Still Having Issues?

If you're still encountering problems, follow the manual setup instructions in the [DEPLOYMENT-GCP.md](DEPLOYMENT-GCP.md) file, which provides step-by-step commands to set up your GCP resources without relying on the setup script. 
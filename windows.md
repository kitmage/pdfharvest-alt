# Running pdfharvest on Windows (Beginner-Friendly Guide)

This guide is written for non-technical users and walks you through everything step by step.

---

## What you need before you start

You need:
- A Windows 10 or Windows 11 computer
- Internet access
- About 20–30 minutes for first-time setup
- An **OpenRouter API key** (used by pdfharvest to process your PDF)

You will install:
- Python
- Tesseract OCR
- Poppler
- pdfharvest

---

## 1) Install Python

1. Open your browser and go to: https://www.python.org/downloads/windows/
2. Download the latest Python 3.10+ installer.
3. Run the installer.
4. **Important:** check the box that says **“Add Python to PATH”**.
5. Click **Install Now**.

After installation, open **PowerShell** and run:

```powershell
python --version
```

If you see a version number (for example `Python 3.11.x`), you are good.

---

## 2) Install Tesseract OCR

pdfharvest needs Tesseract to read text from scanned PDFs.

1. Go to this page and download the Windows installer:
   - https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer with default settings.
3. During install, note the folder path (usually `C:\Program Files\Tesseract-OCR`).

### Add Tesseract to PATH

1. Press **Start** and search for **“Environment Variables”**.
2. Click **“Edit the system environment variables”**.
3. Click **Environment Variables...**
4. Under **System variables**, select **Path** → **Edit** → **New**.
5. Add:

```text
C:\Program Files\Tesseract-OCR
```

6. Click **OK** on all windows.

Close and reopen PowerShell, then test:

```powershell
tesseract --version
```

If you see version info, it is installed correctly.

---

## 3) Install Poppler

pdfharvest also needs Poppler tools.

1. Download a Windows Poppler build from:
   - https://github.com/oschwartz10612/poppler-windows/releases
2. Download the latest `.zip` file.
3. Extract it to a folder, for example:

```text
C:\poppler
```

You should end up with a folder like `C:\poppler\Library\bin`.

### Add Poppler to PATH

1. Open **Environment Variables** again.
2. Edit the **Path** variable.
3. Add:

```text
C:\poppler\Library\bin
```

4. Click **OK** everywhere.

Close and reopen PowerShell, then test:

```powershell
pdfinfo -v
```

If you see Poppler version output, it is ready.

---

## 4) Download pdfharvest

If you have Git installed, run in PowerShell:

```powershell
git clone <paste-the-repository-url-here>
cd pdfharvest
```

If you do not use Git:
1. Download the project ZIP from its GitHub page.
2. Extract it.
3. Open that extracted folder in PowerShell.

---

## 5) Create a virtual environment and install dependencies

In the project folder, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks script execution, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 6) Set your OpenRouter API key

Get your API key from OpenRouter, then run (replace with your real key):

```powershell
$env:OPENROUTER_API_KEY="your_real_api_key_here"
```

> Important: this only sets the key for your current PowerShell window.

---

## 7) Start pdfharvest

Run:

```powershell
streamlit run app.py
```

After a few seconds, your browser should open automatically.
If it does not, copy the local URL shown in PowerShell (usually `http://localhost:8501`) into your browser.

---

## 8) Use the app

1. Upload a PDF.
2. Type what you want to extract (for example: “List all invoice numbers and totals as CSV”).
3. Wait for processing.
4. Download or copy the result.

---

## 9) Next time you want to run it

Open PowerShell in the project folder and run:

```powershell
.\.venv\Scripts\Activate.ps1
$env:OPENROUTER_API_KEY="your_real_api_key_here"
streamlit run app.py
```

---

## Troubleshooting

### `python` is not recognized
- Reinstall Python and make sure **Add Python to PATH** is checked.

### `tesseract` is not recognized
- Confirm `C:\Program Files\Tesseract-OCR` is in PATH.
- Restart PowerShell.

### `pdfinfo` is not recognized
- Confirm `C:\poppler\Library\bin` is in PATH.
- Restart PowerShell.

### PowerShell says running scripts is disabled
Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### The app opens but extraction fails
- Confirm your `OPENROUTER_API_KEY` is correct.
- Try a smaller PDF first.
- Check that internet access is available.

---

## Optional: Save API key permanently (so you do not type it every time)

In PowerShell:

```powershell
setx OPENROUTER_API_KEY "your_real_api_key_here"
```

Then close and reopen PowerShell before running the app again.

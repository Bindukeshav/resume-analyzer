# ResumeAI — Smart Resume Analyzer

A full-stack Flask web app that analyzes your resume against job descriptions using TF-IDF, ATS keyword matching, grammar checking, and AI suggestions.

## Features
- 📄 PDF resume upload & text extraction (pdfplumber)
- 🎯 Job match score via TF-IDF + cosine similarity
- ✅ ATS keyword scoring (40+ tech keywords)
- 📝 Rule-based grammar issue detection
- 🤖 AI suggestions via Anthropic Claude (optional)

## Setup

### 1. Install dependencies
```bash
cd resume_analyzer
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

## Usage
1. **Upload** your resume as a PDF
2. **Enter** the target job role (e.g. "Data Scientist")
3. **Paste** the job description in the text area
4. *(Optional)* Enter your Anthropic API key for AI suggestions
5. Click **Analyze Resume**

## Results
- **Match Score** — How well your resume matches the job description (0–100%)
- **ATS Score** — How many important tech keywords are present
- **Missing Keywords** — Skills to add to improve ATS compatibility
- **Grammar Check** — Potential writing issues detected
- **AI Suggestions** — Personalized improvement tips (requires API key)

## Project Structure
```
resume_analyzer/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Frontend UI
└── uploads/            # Temporary PDF storage (auto-created)
```

## Notes
- API key is used only for the current request and never stored
- PDF files are temporarily saved in /uploads and can be cleared anytime
- Grammar check uses rule-based patterns (no external service needed)

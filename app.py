from flask import Flask, request, jsonify, render_template
import os
import re
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ATS_KEYWORDS = [
    "Python", "SQL", "Machine Learning", "Data Analysis", "Deep Learning",
    "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
    "Data Visualization", "Tableau", "Power BI", "Excel", "Statistics",
    "NLP", "Computer Vision", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
    "Git", "GitHub", "REST API", "Agile", "Scrum", "Communication",
    "Problem Solving", "Leadership", "Teamwork", "Project Management",
    "JavaScript", "React", "Node.js", "Java", "C++", "R", "Spark", "Hadoop",
    "ETL", "Data Warehouse", "A/B Testing", "Feature Engineering"
]

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return None, str(e)
    return text.strip(), None

def calculate_match_score(resume_text, job_description):
    if not resume_text or not job_description:
        return 0.0
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return round(float(similarity[0][0]) * 100, 1)
    except:
        return 0.0

def calculate_ats_score(resume_text):
    resume_lower = resume_text.lower()
    found = []
    missing = []
    for kw in ATS_KEYWORDS:
        if kw.lower() in resume_lower:
            found.append(kw)
        else:
            missing.append(kw)
    score = round((len(found) / len(ATS_KEYWORDS)) * 100, 1)
    return score, found, missing

def check_grammar(resume_text):
    """Simple rule-based grammar checks without language_tool_python dependency"""
    issues = []
    sentences = re.split(r'(?<=[.!?])\s+', resume_text)
    
    # Check for common issues
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
        # Check for double spaces
        if '  ' in sentence:
            issues.append(f"Double space found near: '{sentence[:50]}...'")
        # Check for missing capitalization at sentence start
        if sentence and sentence[0].islower() and len(sentence) > 5:
            issues.append(f"Sentence may lack capitalization: '{sentence[:50]}'")
        # Check for common typos patterns
        if re.search(r'\b(\w+)\s+\1\b', sentence, re.IGNORECASE):
            issues.append(f"Possible repeated word near: '{sentence[:50]}'")
    
    # Check for common grammar patterns
    common_errors = [
        (r'\bi am\b', "Consider using 'I am' with proper capitalization"),
        (r'\brecieved\b', "'recieved' may be a typo for 'received'"),
        (r'\bacheived\b', "'acheived' may be a typo for 'achieved'"),
        (r'\bresponsible of\b', "Use 'responsible for' instead of 'responsible of'"),
        (r'\bexperienced in\b.*\bexperienced in\b', "Repetitive use of 'experienced in'"),
    ]
    for pattern, msg in common_errors:
        if re.search(pattern, resume_text, re.IGNORECASE):
            issues.append(msg)
    
    return len(issues), issues[:10]  # Return count and first 10 issues

def get_ai_suggestions(resume_text, job_role, api_key):
    if not api_key or api_key.strip() == "":
        return None, "No API key provided"
    
    prompt = f"""You are a professional resume coach. Analyze this resume for the role of "{job_role}" and provide 5 specific, actionable improvement suggestions.

Resume:
{resume_text[:3000]}

Provide exactly 5 numbered suggestions to improve this resume for the "{job_role}" role. Be specific and actionable. Format each as:
1. [Suggestion title]: [Detailed explanation]"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data['content'][0]['text'], None
        else:
            return None, f"API Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400
    
    file = request.files['resume']
    job_description = request.form.get('job_description', '')
    job_role = request.form.get('job_role', 'Software Engineer')
    api_key = request.form.get('api_key', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'resume.pdf')
    file.save(filepath)
    
    resume_text, err = extract_text_from_pdf(filepath)
    if err or not resume_text:
        return jsonify({'error': f'Could not extract text from PDF: {err}'}), 400
    
    match_score = calculate_match_score(resume_text, job_description) if job_description else 0
    ats_score, found_kws, missing_kws = calculate_ats_score(resume_text)
    grammar_count, grammar_issues = check_grammar(resume_text)
    ai_suggestions, ai_error = get_ai_suggestions(resume_text, job_role, api_key)
    
    return jsonify({
        'match_score': match_score,
        'ats_score': ats_score,
        'found_keywords': found_kws[:15],
        'missing_keywords': missing_kws[:15],
        'grammar_issues_count': grammar_count,
        'grammar_issues': grammar_issues,
        'ai_suggestions': ai_suggestions,
        'ai_error': ai_error,
        'resume_preview': resume_text[:500] + '...' if len(resume_text) > 500 else resume_text
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

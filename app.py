import os
import re
import fitz  # PyMuPDF
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import json
# Import necessary types for safety settings
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables from the .env file
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Gemini API Configuration ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

# --- AI Model Prompts ---

# This prompt is used for a general analysis of the resume
# The double curly braces {{ and }} are crucial. They "escape" the braces in the JSON example
# so that Python's .format() method ignores them and only formats {resume_text}.
GENERAL_PROMPT = """
You are an expert ATS (Applicant Tracking System) and a professional career coach.
Analyze the provided resume text thoroughly. Your response MUST be a single JSON object enclosed in a ```json markdown block.
Do not output any text or explanation outside of the markdown block.

Example Response:
```json
{{
  "ats_score": 88,
  "strengths": ["Strong project management skills", "Proficient in Python and SQL", "Excellent communication"],
  "feedback": ["Quantify achievements in the experience section", "Add a summary section at the top", "Tailor skills to match the job description"],
  "job_suggestions": ["Data Analyst", "Business Intelligence Analyst", "Project Coordinator"]
}}
```

Resume Text:
{resume_text}
"""

# This prompt is used when a job description is provided for comparison
# The double curly braces are also used here for the same reason.
COMPARISON_PROMPT = """
You are an expert ATS (Applicant Tracking System) and a professional career coach.
Analyze the provided resume text against the given job description. Your response must be a single JSON object enclosed in a ```json markdown block.
Do not output any text or explanation outside of the markdown block.

Example Response:
```json
{{
  "match_score": 75,
  "summary": "The candidate is a good fit but lacks direct experience in cloud platforms mentioned in the job description.",
  "missing_keywords": ["AWS", "Tableau", "Agile Methodology"],
  "tailoring_suggestions": ["Highlight any experience with cloud services, even if academic.", "Add a section for 'Data Visualization' and mention relevant tools.", "Incorporate the term 'Agile' if you have experience with iterative development."]
}}
```

Resume Text:
{resume_text}

Job Description:
{job_description}
"""

# --- Helper Function ---
def clean_json_response(raw_text):
    """
    Finds and extracts a valid JSON object from a raw string,
    which might be wrapped in markdown.
    """
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
    return raw_text.strip()

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main upload page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """Analyzes the uploaded resume."""
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    resume_file = request.files['resume']
    job_description = request.form.get('job_description', '').strip()

    # --- 1. Extract Text from PDF ---
    try:
        resume_text = ""
        with fitz.open(stream=resume_file.read(), filetype="pdf") as doc:
            for page in doc:
                resume_text += page.get_text()
    except Exception as e:
        return jsonify({"error": f"Error parsing PDF: {e}"}), 500

    if not resume_text.strip():
        return jsonify({"error": "Could not extract text from the provided PDF"}), 400

    # --- 2. Call the Gemini API ---
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        
        if job_description:
            prompt = COMPARISON_PROMPT.format(resume_text=resume_text, job_description=job_description)
        else:
            prompt = GENERAL_PROMPT.format(resume_text=resume_text)

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        generation_config = {
            "candidate_count": 1,
            "response_mime_type": "text/plain",
        }

        response = model.generate_content(
            prompt, 
            safety_settings=safety_settings,
            generation_config=generation_config
        )
        
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            error_message = f"Analysis failed: The content was blocked for safety reasons ({block_reason})."
            return jsonify({"error": error_message}), 400

        response_text = "".join(part.text for part in response.parts)

        if not response_text:
            error_message = "Analysis failed: The AI model returned an empty response."
            return jsonify({"error": error_message}), 400
        
        cleaned_response = clean_json_response(response_text)
        
        return cleaned_response, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        print(f"--- SERVER CRASH ---")
        print(f"An unexpected server error occurred: {e}")
        import traceback
        traceback.print_exc()
        print(f"--- END TRACEBACK ---")
        return jsonify({"error": f"An unexpected server error occurred. Please check the terminal for details. Error: {str(e)}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)


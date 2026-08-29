# Automated Resume Parser

Complete Flask project for the CodeTech-style Automated Resume Parser task.

### Features
- PDF and DOCX upload
- Text extraction using pdfplumber/python-docx
- spaCy-based name extraction with fallback
- Email and phone extraction
- Skill and education categorization
- Saved candidate records
- Browser UI

### Windows setup
```bat
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
```
Open `http://127.0.0.1:5000`.

The demo uses SQLite so it runs immediately. `psycopg2-binary` is included for PostgreSQL integration if required by deployment.

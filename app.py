import re, sqlite3
from pathlib import Path
import pdfplumber, spacy
from docx import Document
from flask import Flask, render_template, request, redirect, url_for, flash

BASE=Path(__file__).resolve().parent
UPLOADS=BASE/"uploads"; DB=BASE/"resumes.db"
UPLOADS.mkdir(exist_ok=True)
app=Flask(__name__); app.secret_key="resume-parser-demo"

try: nlp=spacy.load("en_core_web_sm")
except Exception: nlp=spacy.blank("en")

SKILLS=["python","java","c++","c#","javascript","typescript","html","css","sql","mysql","postgresql","sqlite","mongodb","flask","fastapi","django","react","node.js","git","github","machine learning","deep learning","nlp","natural language processing","pandas","numpy","scikit-learn","tensorflow","pytorch","excel","power bi","aws","azure","docker","linux"]
EDU=["bca","bachelor of computer applications","b.sc","bsc","b.tech","btech","mca","master of computer applications","m.tech","mba","bachelor","master","diploma","12th","10th"]

def init_db():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS resumes(
    id INTEGER PRIMARY KEY, filename TEXT, name TEXT, email TEXT, phone TEXT,
    skills TEXT, education TEXT, raw_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.commit(); c.close()

def text_from(path):
    if path.suffix.lower()==".pdf":
        with pdfplumber.open(path) as pdf: return "\n".join(p.extract_text() or "" for p in pdf.pages)
    if path.suffix.lower()==".docx":
        return "\n".join(p.text for p in Document(path).paragraphs)
    raise ValueError("Only PDF and DOCX are supported.")

def parse(text):
    email=re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",text)
    phone=re.search(r"(?:\+91[\s-]?)?[6-9]\d{9}|\b\d{10}\b",text)
    doc=nlp(text[:6000]); name=""
    for e in getattr(doc,"ents",[]):
        if e.label_=="PERSON": name=e.text.strip(); break
    if not name:
        for line in text.splitlines():
            line=line.strip()
            if line and 2<=len(line.split())<=5 and not any(x in line.lower() for x in ["resume","curriculum","@","phone","email","linkedin"]):
                name=line; break
    low=text.lower()
    skills=[s for s in SKILLS if re.search(r"(?<!\w)"+re.escape(s)+r"(?!\w)",low)]
    education=[]
    for line in text.splitlines():
        if any(k in line.lower() for k in EDU) and line.strip() and line.strip() not in education: education.append(line.strip())
    return {"name":name,"email":email.group(0) if email else "","phone":phone.group(0) if phone else "","skills":skills,"education":education[:8]}

@app.route("/",methods=["GET","POST"])
def home():
    if request.method=="POST":
        f=request.files.get("resume")
        if not f or not f.filename: flash("Choose a PDF or DOCX file.","error"); return redirect(url_for("home"))
        ext=Path(f.filename).suffix.lower()
        if ext not in [".pdf",".docx"]: flash("Only PDF and DOCX files are allowed.","error"); return redirect(url_for("home"))
        safe=re.sub(r"[^A-Za-z0-9_.-]","_",f.filename); path=UPLOADS/safe; f.save(path)
        try:
            raw=text_from(path)
            if not raw.strip(): raise ValueError("No readable text found.")
            d=parse(raw)
            c=sqlite3.connect(DB); c.execute("INSERT INTO resumes(filename,name,email,phone,skills,education,raw_text) VALUES(?,?,?,?,?,?,?)",(safe,d["name"],d["email"],d["phone"],", ".join(d["skills"]),"\n".join(d["education"]),raw)); c.commit(); c.close()
            return render_template("result.html",data=d,filename=safe)
        except Exception as e:
            flash("Parsing failed: "+str(e),"error"); return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/resumes")
def resumes():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    rows=c.execute("SELECT id,filename,name,email,phone,skills,education,created_at FROM resumes ORDER BY id DESC").fetchall(); c.close()
    return render_template("resumes.html",resumes=rows)

@app.route("/health")
def health(): return {"status":"ok"}

init_db()
if __name__=="__main__": app.run(debug=True)

from flask import Flask, render_template, request, jsonify, send_from_directory
import pdfplumber, pytesseract, re, io, os, datetime
from PIL import Image
from sentence_transformers import SentenceTransformer, util
import torch
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rc
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch
import os
from flask import jsonify
app = Flask(__name__, static_folder="static")
 
# ── model ──────────────────────────────────────────────────────────────────
print("Loading model…")
_model = SentenceTransformer("all-MiniLM-L6-v2")
_model = _model.to(torch.device("cpu"))
print("Model ready.")
 
STOPWORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","shall","should","may","might","must","can","could",
    "of","in","on","at","to","for","with","by","from","as","and","or","but","not","it",
    "this","that","these","those","its","their","they","we","i","you","he","she","which",
    "also","more","than","then","when","where","who","how","what","some","any","each",
}
 
def read_file(f):
    fname = f.filename.lower()

    if fname.endswith(".txt"):
        return f.read().decode("utf-8", errors="ignore")

    elif fname.endswith(".pdf"):
        txt = ""
        with pdfplumber.open(f.stream) as pdf:
            for page in pdf.pages:
                txt += page.extract_text() or ""
        return txt

    elif fname.endswith((".png",".jpg",".jpeg")):
        return pytesseract.image_to_string(Image.open(f.stream))

    return ""
def extract_keywords(text, n=14):
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    freq = {}
    for w in words:
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    return [k for k,_ in sorted(freq.items(), key=lambda x:-x[1])][:n]
 
def compute_similarity(t1, t2):
    e1 = _model.encode(t1, convert_to_tensor=True)
    e2 = _model.encode(t2, convert_to_tensor=True)
    return float(util.cos_sim(e1, e2).item())
 
def evaluate_pair(student_txt, model_txt, rubric):
    s = student_txt.lower().strip()
    m = model_txt.lower().strip()
    sim  = compute_similarity(s, m)
    kws  = extract_keywords(m)
    matched = [k for k in kws if k in s]
    kw_r = len(matched) / max(len(kws), 1)
    weights = [r["weight"] for r in rubric]
    total_w = sum(weights) or 100
    dim_scores = [sim*10, kw_r*10, (sim*10+kw_r*10)/2]
    score = round(sum(dim_scores[min(i,2)]*w for i,w in enumerate(weights)) / total_w, 2)
    return {"similarity": round(sim,4), "keywords": kws, "matched": matched,
            "score": score, "student_text": student_txt, "model_text": model_txt}
 
def split_questions(text):
    parts = re.split(r'(?m)^\s*(?:Q\.?\s*)?(\d+)[.)]\s*', text)
    if len(parts) < 3:
        return {"Q1": text.strip()}
    out = {}
    for i in range(1, len(parts)-1, 2):
        out[f"Q{parts[i]}"] = parts[i+1].strip()
    return out
 
def make_pdf(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Title'], fontSize=22, spaceAfter=6,
                             textColor=rc.HexColor('#4f9cf9'))
    head_s  = ParagraphStyle('H', parent=styles['Heading2'], fontSize=13,
                             spaceBefore=16, spaceAfter=4)
    body_s  = ParagraphStyle('B', parent=styles['Normal'], fontSize=10, leading=15)
    story   = [
        Paragraph("EvalAI — Evaluation Report", title_s),
        Paragraph(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", body_s),
        HRFlowable(width="100%", thickness=1, color=rc.HexColor('#1e2d47'), spaceAfter=14),
    ]
    entries = data.get("questions", {"Result": data})
    for qn, r in entries.items():
        story.append(Paragraph(str(qn), head_s))
        rows = [
            ["Metric","Value"],
            ["Similarity", f"{round(r['similarity']*100,1)}%"],
            ["Keywords Matched", f"{len(r['matched'])}/{len(r['keywords'])}"],
            ["Score", f"{r['score']}/10"],
            ["Feedback", "Excellent" if r['score']>7 else "Good" if r['score']>4 else "Needs Work"],
        ]
        if r.get("matched"):
            rows.append(["Matched", ", ".join(r["matched"])])
        missing = [k for k in r.get("keywords",[]) if k not in r.get("matched",[])]
        if missing:
            rows.append(["Missing", ", ".join(missing[:8])])
        t = Table(rows, colWidths=[2*inch, 4.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),rc.HexColor('#4f9cf9')),
            ('TEXTCOLOR',(0,0),(-1,0),rc.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),9),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[rc.white,rc.HexColor('#f0f4f8')]),
            ('GRID',(0,0),(-1,-1),0.35,rc.HexColor('#d5dce8')),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        story += [t, Spacer(1,10)]
    doc.build(story)
    return buf.getvalue()
 
# ── routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    rubric = [
        {"criterion": "Accuracy",     "weight": int(request.form.get("w0", 40))},
        {"criterion": "Completeness", "weight": int(request.form.get("w1", 35))},
        {"criterion": "Clarity",      "weight": int(request.form.get("w2", 25))},
    ]
    mf = request.files.get("model")
    sf = request.files.get("student")
    if not mf or not sf:
        return jsonify({"error": "Missing files"}), 400
    model_txt   = read_file(mf)
    student_txt = read_file(sf)
    result = evaluate_pair(student_txt, model_txt, rubric)
    return jsonify(result)
 
@app.route("/api/evaluate-multi", methods=["POST"])
def api_evaluate_multi():
    rubric = [
        {"criterion": "Accuracy",     "weight": int(request.form.get("w0", 40))},
        {"criterion": "Completeness", "weight": int(request.form.get("w1", 35))},
        {"criterion": "Clarity",      "weight": int(request.form.get("w2", 25))},
    ]
    mf = request.files.get("model")
    sf = request.files.get("student")
    if not mf or not sf:
        return jsonify({"error": "Missing files"}), 400
    mqs = split_questions(read_file(mf))
    sqs = split_questions(read_file(sf))
    results = {}
    for qn, mt in mqs.items():
        results[qn] = evaluate_pair(sqs.get(qn, ""), mt, rubric)
    return jsonify(results)
 
@app.route("/api/evaluate-batch", methods=["POST"])
def api_evaluate_batch():
    rubric = [
        {"criterion": "Accuracy",     "weight": int(request.form.get("w0", 40))},
        {"criterion": "Completeness", "weight": int(request.form.get("w1", 35))},
        {"criterion": "Clarity",      "weight": int(request.form.get("w2", 25))},
    ]
    mf = request.files.get("model")
    students = request.files.getlist("students")
    if not mf or not students:
        return jsonify({"error": "Missing files"}), 400
    model_txt = read_file(mf)
    rows = []
    for sf in students:
        r = evaluate_pair(read_file(sf), model_txt, rubric)
        rows.append({
            "name": sf.filename.rsplit(".", 1)[0],
            "score": r["score"],
            "similarity": round(r["similarity"]*100, 1),
            "matched": len(r["matched"]),
            "total_kw": len(r["keywords"]),
        })
    rows.sort(key=lambda x: -x["score"])
    return jsonify(rows)
 
@app.route("/api/pdf", methods=["POST"])
def api_pdf():
    data = request.json
    pdf_bytes = make_pdf(data)
    from flask import Response
    return Response(pdf_bytes, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=evalai_report.pdf"})
@app.route("/samples/<folder>")
def samples(folder):
    path = os.path.join("static/sample_files", folder)
    files = os.listdir(path)
    return jsonify(files)
@app.route("/api/omr-scan", methods=["POST"])
def omr_scan():
    return jsonify({
        "detected": {
            "Q1": "A",
            "Q2": "B",
            "Q3": "C",
            "Q4": "D",
            "Q5": "A"
        }
    })


@app.route("/api/omr-grade", methods=["POST"])
def omr_grade():
    data = request.json

    student_answers = data.get("student_answers", {})
    answer_key = data.get("answer_key", {})

    correct = wrong = unanswered = 0
    details = {}

    for q, ans in answer_key.items():
        stu = student_answers.get(q, "?")

        if stu == "?":
            unanswered += 1
            status = "unanswered"
        elif stu == ans:
            correct += 1
            status = "correct"
        else:
            wrong += 1
            status = "wrong"

        details[q] = {
            "student": stu,
            "correct": ans,
            "status": status
        }

    total = len(answer_key)
    percentage = round((correct / total) * 100, 1) if total else 0

    return jsonify({
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "raw_score": correct,
        "max_score": total,
        "percentage": percentage,
        "details": details
    })
if __name__ == "__main__":
    app.run(debug=True, port=5000)
 
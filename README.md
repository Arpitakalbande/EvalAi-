[README (1).md](https://github.com/user-attachments/files/27125862/README.1.md)[Uploading READ# 🎓 EvalAI — Intelligent Exam Evaluator

> AI-powered examination evaluation platform for subjective answers, OMR sheets, and batch class grading.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)
![NLP](https://img.shields.io/badge/NLP-Sentence--Transformers-a78bfa?style=flat)

---

## Overview

EvalAI is a full-stack web application that automates exam evaluation using semantic NLP, computer vision, and optional Claude AI feedback. Designed for educators, coaching institutes, and examination boards — it grades subjective answers, scans OMR bubble sheets, and processes entire classrooms in seconds.

---

## Features

| Feature | Description |
|---|---|
| **📝 Subjective Evaluation** | Semantic similarity scoring between model and student answers using `all-MiniLM-L6-v2` |
| **🔘 OMR / MCQ Scanner** | Upload a scanned bubble sheet; OpenCV detects filled circles automatically |
| **🗂 Multi-Question Mode** | Auto-parses numbered questions (Q1, Q2…) and evaluates each independently |
| **👥 Batch Class Grading** | Grade an entire class from one model answer + multiple student files |
| **✨ Claude AI Feedback** | Anthropic Claude generates paragraph-level improvement suggestions |
| **📋 Session History** | Score trends, comparison charts, and full PDF report export |
| **📑 PDF / CSV Export** | ReportLab-generated styled PDF reports and CSV leaderboards |

---

## Tech Stack

**Backend**
- [Flask](https://flask.palletsprojects.com/) — lightweight Python web framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF text extraction
- [pytesseract](https://github.com/madmaze/pytesseract) — OCR for image-based answers
- [Sentence-Transformers](https://www.sbert.net/) — semantic similarity via `all-MiniLM-L6-v2`
- [ReportLab](https://www.reportlab.com/) — PDF report generation
- [PyTorch](https://pytorch.org/) — tensor computation for embeddings

**Frontend**
- Vanilla HTML/CSS/JavaScript — zero framework dependencies
- [Plotly.js](https://plotly.com/javascript/) — radar charts, gauges, histograms, pie charts
- Google Fonts — Outfit + JetBrains Mono

---

## Project Structure

```
evalai/
├── app.py                  # Flask application & API routes
├── templates/
│   └── index.html          # Single-page frontend
├── static/
│   ├── sample_files/
│   │   ├── subjective/     # Sample model & student answer .txt files
│   │   ├── omr/            # Sample OMR sheet images & answer keys
│   │   └── batch/          # Sample student files for batch grading
│   └── ...
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Tesseract OCR installed on your system

**Install Tesseract:**
```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/evalai.git
cd evalai

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

The app will be available at `http://localhost:5000`.

---

## Dependencies

Create a `requirements.txt` with the following:

```
flask
pdfplumber
pytesseract
Pillow
sentence-transformers
torch
reportlab
```

---

## API Reference

### `POST /api/evaluate`
Evaluate a single student answer against a model answer.

| Field | Type | Description |
|---|---|---|
| `model` | File | Model/reference answer file (`.txt`, `.pdf`, `.png`, `.jpg`) |
| `student` | File | Student answer file |
| `w0`, `w1`, `w2` | int | Rubric weights for Accuracy, Completeness, Clarity (default: 40, 35, 25) |

**Response:**
```json
{
  "similarity": 0.842,
  "keywords": ["photosynthesis", "chlorophyll", "glucose"],
  "matched": ["photosynthesis", "chlorophyll"],
  "score": 7.45,
  "student_text": "...",
  "model_text": "..."
}
```

---

### `POST /api/evaluate-multi`
Evaluate a multi-question answer sheet (auto-parses `Q1.`, `Q2.`… format).

Same fields as `/api/evaluate`. Returns a JSON object keyed by question number.

---

### `POST /api/evaluate-batch`
Grade multiple students against a single model answer.

| Field | Type | Description |
|---|---|---|
| `model` | File | Model answer file |
| `students` | File[] | Multiple student answer files |

**Response:** Array of student results sorted by score descending.

---

### `POST /api/omr-scan`
Scan an OMR sheet image and detect filled bubbles.

| Field | Type | Description |
|---|---|---|
| `omr_image` | File | Scanned OMR sheet (`.png`, `.jpg`) |
| `num_questions` | int | Number of questions |
| `options_per_q` | int | Options per question (3, 4, or 5) |

---

### `POST /api/omr-grade`
Grade detected OMR answers against an answer key with a marking scheme.

```json
{
  "student_answers": { "Q1": "A", "Q2": "C" },
  "answer_key":      { "Q1": "A", "Q2": "B" },
  "marking_scheme":  { "correct": 4, "wrong": -1, "unanswered": 0 }
}
```

---

### `POST /api/pdf`
Generate a styled PDF report from evaluation results. Returns binary PDF.

---

## Supported File Formats

| Format | Extraction Method |
|---|---|
| `.txt` | Direct UTF-8 read |
| `.pdf` | `pdfplumber` text extraction |
| `.png` / `.jpg` / `.jpeg` | `pytesseract` OCR |

---

## Scoring Algorithm

The final score is computed as a weighted combination of:

1. **Semantic Similarity** — cosine similarity between sentence embeddings of model and student answers
2. **Keyword Match Rate** — ratio of top-N model keywords found in the student answer
3. **Combined Dimension** — average of the two above

Weights are configurable via the rubric sliders (Accuracy / Completeness / Clarity).

---

## Answer Format for Multi-Question Mode

Number your questions using any of these formats:

```
Q1. Answer text for question one.
Q2. Answer text for question two.

1. Answer text for question one.
2. Answer text for question two.
```

---

## OMR Marking Schemes

| Scheme | Correct | Wrong | Blank |
|---|---|---|---|
| JEE Main | +4 | −1 | 0 |
| NEET | +4 | −1 | 0 |
| Simple | +1 | 0 | 0 |
| Custom | user-defined | user-defined | user-defined |

---

## Claude AI Feedback

Enable the **✨ Claude AI Feedback** toggle in the UI to receive paragraph-level improvement suggestions powered by Anthropic's Claude API. Requires a valid API key configured on the backend.

---

## Contributing

Contributions are welcome. Please open an issue to discuss your proposed changes before submitting a pull request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- [Sentence-Transformers](https://www.sbert.net/) by UKPLab for the `all-MiniLM-L6-v2` model
- [Anthropic Claude](https://www.anthropic.com/) for AI-generated feedback
- [Plotly](https://plotly.com/) for interactive charts
ME (1).md…]()

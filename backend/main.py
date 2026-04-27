from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import pdfplumber
import os
from docx import Document
from transformers import pipeline

app = FastAPI()

# Load Hugging Face QA model once
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF, DOCX, or TXT files."""
    try:
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {repr(e)}")

def evaluate_answer(answer: str, question: str, context: str, score: float) -> dict:
    """Simple evaluation metrics for QA answers."""
    metrics = {
        "accuracy": 0.0,
        "relevance": 0.0,
        "reasoning_difficulty": 0.0
    }

    # Accuracy: based on confidence score
    metrics["accuracy"] = round(score * 100, 2)

    # Relevance: check if answer words appear in context
    metrics["relevance"] = round(
        (len([w for w in answer.split() if w.lower() in context.lower()]) / max(1, len(answer.split()))) * 100, 2
    )

    # Reasoning difficulty: heuristic based on question length
    q_len = len(question.split())
    if q_len <= 3:
        metrics["reasoning_difficulty"] = 20.0
    elif q_len <= 7:
        metrics["reasoning_difficulty"] = 50.0
    else:
        metrics["reasoning_difficulty"] = 80.0

    return metrics

@app.post("/ask")
async def ask_question(file: UploadFile, question: str = Form(...)):
    """Accept a file + question, return QA answer + evaluation metrics."""
    try:
        # Save uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Extract text
        context = extract_text_from_file(file_path)
        os.remove(file_path)

        if not context.strip():
            raise HTTPException(status_code=400, detail="Document is empty or unreadable")

        # Run Hugging Face QA
        answer = qa_pipeline(question=question, context=context)

        # Evaluate answer
        metrics = evaluate_answer(answer.get("answer", ""), question, context, answer.get("score", 0.0))

        return JSONResponse({
            "filename": file.filename,
            "question": question,
            "answer": answer.get("answer", ""),
            "score": float(answer.get("score", 0.0)),
            "metrics": metrics
        })
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {repr(e)}")

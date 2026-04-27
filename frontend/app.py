import streamlit as st
import requests

st.title("AI Document Evaluator")

uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
question = st.text_input("Ask a question about the document")

if uploaded_file and question:
    with st.spinner("Processing..."):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        data = {"question": question}
        # Use your deployed backend URL instead of localhost
        response = requests.post("https://doc-evaluator.fly.dev/ask", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            st.subheader("Results")
            st.write(f"**Filename:** {result['filename']}")
            st.write(f"**Question:** {result['question']}")
            st.write(f"**Answer:** {result['answer']}")
            st.write(f"**Confidence Score:** {result['score']:.4f}")

            st.subheader("Evaluation Metrics")
            st.write(f"Accuracy: {result['metrics']['accuracy']}%")
            st.write(f"Relevance: {result['metrics']['relevance']}%")
            st.write(f"Reasoning Difficulty: {result['metrics']['reasoning_difficulty']}%")
        else:
            st.error(f"Error: {response.text}")

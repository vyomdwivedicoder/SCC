# Student Command Center (SCC)

Student Command Center (SCC) is an AI-powered toolbox designed to help students be more productive, get clean study notes, brainstorm ideas, and manage simple finances. Built with **Streamlit** and the **Groq** API (LLaMA 3.1), the app is beginner-friendly and hackathon-ready.

---

## Features

### Task Splitter
- Paste a complex task and get a clear sequence of actionable steps.
- Steps are shown only (they are **not** automatically added to the todo list).

### Todo List (Manual)
- Add tasks manually and mark them done.
- Download your todo list as a `.txt` file.

### Idea Generator
- Choose a category or enter a custom prompt to generate 10 creative and practical ideas.

### Notes Cleaner
- Upload PDF or paste unstructured notes.
- AI cleans and formats notes for study and exports cleaned notes as PDF.

### Finance Manager
- Add expenses, view the table, download as Excel, and get AI-powered financial tips.

---

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
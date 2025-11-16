import streamlit as st
from groq import Groq
import re
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import PyPDF2

# -----------------------------------------------------------
# PAGE CONFIG (must be first Streamlit command)
# -----------------------------------------------------------
st.set_page_config(page_title="Student Command Center", page_icon="📚", layout="wide")

# -----------------------------------------------------------
# LOAD CSS (after set_page_config)
# -----------------------------------------------------------
def load_css(file_name="style.css"):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        # If the CSS file is missing, continue without crashing.
        st.warning("style.css not found — continuing with default styling.")

load_css("style.css")

# -----------------------------------------------------------
# GROQ CLIENT (reads API key from Streamlit secrets)
# -----------------------------------------------------------
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    client = None
    st.warning("GROQ API key not found in secrets. Some AI features will not work until you add GROQ_API_KEY to .streamlit/secrets.toml")

# -----------------------------------------------------------
# AI CALL (using Groq LLaMA 3.1 if available)
# -----------------------------------------------------------
def ai_call(prompt: str) -> str:
    """
    Sends prompt to Groq (if configured) and returns text.
    If Groq client is not available, returns a helpful placeholder message.
    """
    if client is None:
        return "AI unavailable — add your GROQ_API_KEY in .streamlit/secrets.toml to enable AI features."
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant"
    )
    # Defensive parsing
    try:
        return response.choices[0].message.content.strip()
    except Exception:
        # Some SDK responses may use a different field
        try:
            return response.choices[0].message.content.strip()
        except Exception:
            return str(response)

# -----------------------------------------------------------
# CLEAN GENERATED STEPS
# -----------------------------------------------------------
def clean_step(step: str) -> str:
    """
    Remove bullets, markdown symbols, numbers, arrows, and extra whitespace.
    """
    step = re.sub(r"^[\*\-\•\·\→\▶\»]+\s*", "", step)   # remove bullets and special chars at start
    step = re.sub(r"^\d+\.\s*", "", step)               # remove "1. " numbering
    step = re.sub(r"^\(\d+\)\s*", "", step)             # remove "(1)" style numbering
    return step.strip()

# -----------------------------------------------------------
# PDF GENERATION
# -----------------------------------------------------------
def generate_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        # ensure we write even long lines
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest="S").encode("latin1")

# -----------------------------------------------------------
# EXTRACT TEXT FROM PDF
# -----------------------------------------------------------
def extract_text_from_pdf(uploaded_file) -> str:
    text = ""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            try:
                p = page.extract_text()
                if p:
                    text += p + "\n"
            except Exception:
                # ignore page extraction errors
                pass
    except Exception:
        pass
    return text

# -----------------------------------------------------------
# SESSION STATE INIT
# -----------------------------------------------------------
if "todos" not in st.session_state:
    st.session_state.todos = []

if "finance" not in st.session_state:
    st.session_state.finance = []

if "cleaned_notes" not in st.session_state:
    st.session_state.cleaned_notes = ""

# -----------------------------------------------------------
# APP LAYOUT: Tabs
# -----------------------------------------------------------
tabs = st.tabs([
    "📝 Task Splitter",
    "🗂️ Todo List",
    "💡 Idea Generator",
    "📚 Notes Cleaner",
    "💰 Finance Manager"
])

# -----------------------------------------------------------
# TAB 1 — TASK SPLITTER (Only shows steps; does NOT add to todo list)
# -----------------------------------------------------------
with tabs[0]:
    st.header("📝 Task Splitter")
    st.write("Paste a complex task and get a clean list of actionable steps. Steps are shown here only — they are NOT added automatically to your Todo List.")

    main_task = st.text_input("Enter the task you'd like broken down", placeholder="e.g., Prepare final year project presentation")

    if st.button("Generate Steps"):
        if main_task.strip():
            raw_steps = ai_call(f"Break this task into a clear sequence of simple, actionable steps for a student:\n\n{main_task}")
            # split and clean
            steps = []
            for s in raw_steps.split("\n"):
                cs = clean_step(s)
                if cs:
                    steps.append(cs)
            if steps:
                st.write("### Steps to complete the task")
                for idx, s in enumerate(steps, start=1):
                    st.markdown(f"**{idx}.** {s}")
            else:
                st.info("No steps generated. Try rewording the task or check your API key.")
        else:
            st.error("Please enter a task to generate steps.")

# -----------------------------------------------------------
# TAB 2 — TODO LIST (Manual add/remove only)
# -----------------------------------------------------------
with tabs[1]:
    st.header("🗂️ Todo List (Manual)")
    st.write("Add tasks manually. Use the checkboxes to mark tasks done — completed tasks will be removed from the list.")

    col1, col2 = st.columns([4,1])
    with col1:
        new_task = st.text_input("Add a new task", placeholder="e.g., Finish project report")
    with col2:
        if st.button("Add Task"):
            if new_task.strip():
                st.session_state.todos.append(new_task.strip())
                st.success("Task added.")
            else:
                st.error("Enter a task to add.")

    st.subheader("Your Tasks")
    to_remove = []
    for i, t in enumerate(st.session_state.todos):
        if st.checkbox(t, key=f"manual_todo_{i}"):
            to_remove.append(t)

    if to_remove:
        for r in to_remove:
            if r in st.session_state.todos:
                st.session_state.todos.remove(r)
        st.success("Removed completed tasks.")

    # download button using Streamlit's download_button
    if st.session_state.todos:
        todo_text = "\n".join(st.session_state.todos)
        st.download_button(
            label="Download Todo List (TXT)",
            data=todo_text,
            file_name="todo_list.txt",
            mime="text/plain"
        )

# -----------------------------------------------------------
# TAB 3 — IDEA GENERATOR (category + custom prompt)
# -----------------------------------------------------------
with tabs[2]:
    st.header("💡 Idea Generator")
    st.write("Choose a category or enter a custom prompt. If a custom prompt is entered, it will be used instead of the category.")

    col_a, col_b = st.columns(2)
    with col_a:
        category = st.selectbox("Choose idea category", ["Study Ideas", "Project Ideas", "Personal Goals", "Time Management Tips", "Event/Club Ideas"])
    with col_b:
        custom_prompt = st.text_input("Optional: Custom prompt (overrides category)", placeholder="e.g., Project ideas using sensors for environmental monitoring")

    if st.button("Generate Ideas"):
        if custom_prompt.strip():
            prompt = f"Generate 10 concise, practical, and creative ideas based on this prompt:\n\n{custom_prompt}"
        else:
            prompt = f"Generate 10 concise and practical ideas for: {category}"
        ideas = ai_call(prompt)
        st.write("### ✨ Generated Ideas")
        st.write(ideas)

# -----------------------------------------------------------
# TAB 4 — NOTES CLEANER (PDF upload + paste + export PDF)
# -----------------------------------------------------------
with tabs[3]:
    st.header("📚 Notes Cleaner")
    st.write("Upload a PDF or paste text. Click 'Clean Notes' to get well formatted notes suitable for revision. You can export cleaned notes as PDF.")

    uploaded_pdf = st.file_uploader("Upload PDF (optional)", type=["pdf"])
    pasted = st.text_area("Or paste notes here", height=200)

    source_text = ""
    if uploaded_pdf:
        source_text = extract_text_from_pdf(uploaded_pdf)
        if source_text.strip():
            st.success("Extracted text from PDF.")
        else:
            st.info("PDF uploaded but no extractable text found; try pasting notes instead.")

    elif pasted.strip():
        source_text = pasted

    if st.button("Clean Notes"):
        if source_text.strip():
            cleaned = ai_call(f"Clean, organize, and format these notes for studying. Make headings and bullet points where appropriate:\n\n{source_text}")
            st.session_state.cleaned_notes = cleaned
            st.write("### 📘 Cleaned Notes")
            st.write(cleaned)
        else:
            st.error("Please upload a PDF or paste notes to clean.")

    if st.session_state.cleaned_notes:
        pdf_bytes = generate_pdf(st.session_state.cleaned_notes)
        st.download_button(
            label="Download Cleaned Notes as PDF",
            data=pdf_bytes,
            file_name="cleaned_notes.pdf",
            mime="application/pdf"
        )

# -----------------------------------------------------------
# TAB 5 — FINANCE MANAGER
# -----------------------------------------------------------
with tabs[4]:
    st.header("💰 Finance Manager")
    st.write("Track expenses and get a short AI-powered financial suggestion based on your listed expenses.")

    c1, c2, c3 = st.columns([2,4,2])
    with c1:
        date_input = st.date_input("Date")
    with c2:
        desc_input = st.text_input("Description")
    with c3:
        amt_input = st.number_input("Amount", min_value=0.0, step=1.0)

    category_input = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Education", "Other"])

    if st.button("Add Expense"):
        st.session_state.finance.append({
            "date": str(date_input),
            "description": desc_input,
            "amount": float(amt_input),
            "category": category_input
        })
        st.success("Expense added.")

    if st.session_state.finance:
        df = pd.DataFrame(st.session_state.finance)
        st.subheader("Your expense table")
        st.dataframe(df)

        # Download expenses as Excel
        out = BytesIO()
        df.to_excel(out, index=False)
        st.download_button(
            "Download Expenses (Excel)",
            data=out.getvalue(),
            file_name="expenses.xlsx"
        )

        if st.button("Get Financial Advice"):
            advice = ai_call(f"Here are my expenses (student):\n\n{df.to_string(index=False)}\n\nGive simple, actionable suggestions to save money and manage budget.")
            st.write("### 💡 Suggestions")
            st.write(advice)

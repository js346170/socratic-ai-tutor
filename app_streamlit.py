# app_streamlit.py
import streamlit as st
import json
import csv
from datetime import datetime
import uuid
import pandas as pd

# -----------------------------
# Flowchart definition
# -----------------------------
flowchart_steps = [
    {  # Step 0
        "id": "get_student_info",
        "prompt": (
            "Welcome to your Self Reflective Learning Coach. Our goal is to show you an effective method "
            "for using AI for problem solving. For now, follow our programs prompts, in the future you can "
            "do this without our help! Let's get set up. What's your grade level and course? "
            "(e.g., '11th Grade, AP Microeconomics')"
        ),
        "input_needed": True,
        "next_step": "get_problem"
    },
    {  # Step 1
        "id": "get_problem",
        "prompt": (
            "What specific problem are you working on? Paste it below or if it is a screenshot, paste directly into the AI"
        ),
        "input_needed": True,
        "next_step": "prime_ai"
    },
    {  # Step 2
        "id": "prime_ai",
        "prompt": (
            "CRUCIAL FIRST STEP:\n"
            "1. Open ChatGPT or Claude in your web browser.\n"
            "2. If you have a screenshot of the problem, upload it to the AI first.\n"
            "3. Copy the message below and paste it into the AI.\n"
            "4. Come back here and click 'Next' after you've done this."
        ),
        "input_needed": False,
        "next_step": "concept_review",
        "priming_message": (
            "Please act as a Socratic tutor. I've provided the problem above. Do not give me the final answer. "
            "Help me learn by asking guiding questions, clarifying concepts, and breaking the problem into smaller steps."
        )
    },
    {  # Step 3
        "id": "concept_review",
        "prompt": (
            "Now let's prepare. Based on your problem, what main concepts do you need to understand?\n\n"
            "Examples:\n- 'Supply and demand curves'\n- 'Price elasticity calculation' \n- 'Deadweight loss formula'\n"
            "- 'Market equilibrium points'\n\n"
            "List any concepts you're unsure about (or type 'none' if you're confident):"
        ),
        "input_needed": True,
        "next_step": "first_step_strategy"
    },
    {  # Step 4
        "id": "first_step_strategy",
        "prompt": (
            "Do you know what the FIRST STEP should be to solve this problem?\n\n"
            "- If YES: Type 'yes' and we'll help you work through it step-by-step\n"
            "- If NO: Type 'no' and we'll ask the AI for just the first step"
        ),
        "input_needed": True,
        "next_step": "perform_work",  # harmless default; we handle branching in code
        "yes_message": (
            "Great! Work with the AI to complete as much as you can. When you get stuck, come back and tell me "
            "where you need help.\n\n"
            "Copy this to the AI: 'Help me work through this problem step-by-step without giving me the final answer. "
            "Start with the first step. Remember you are scaffolding my learning.'"
        ),
        "no_message": (
            "No problem! Let's get some guidance on where to start.\n\n"
            "Copy this to the AI: 'What should be the very first step to solve this problem? Please explain it without "
            "solving the whole thing. Remember, you are scaffolding my learning.'"
        )
    },
    {  # Step 5
        "id": "perform_work",
        "prompt": (
            "Now work on that first step with the AI's help. When you're ready, come back and tell me what you did "
            "or what you learned:"
        ),
        "input_needed": True,
        "next_step": "continue_or_complete"
    },
    {  # Step 6
        "id": "continue_or_complete",
        "prompt": (
            "Great progress! Do you want to:\n1. Continue to the next step\n2. Review your work so far\n3. You've completed the problem"
        ),
        "input_needed": True,
        "next_step": None
    }
]

# O(1) lookup
STEP_BY_ID = {s["id"]: s for s in flowchart_steps}
def get_step(step_id): return STEP_BY_ID.get(step_id)

FIELDNAMES = [
    "session_id", "timestamp", "step_index", "step_id",
    "grade_level", "problem_text", "concepts_reviewed",
    "knew_first_step", "work_notes", "completion_choice"
]
# -----------------------------
# Helpers
# -----------------------------
def _yn(s: str = None):
    s = (s or "").strip().lower()
    if s in {"y", "yes", "yeah", "yep", "1"}: return "yes"
    if s in {"n", "no", "nope", "0"}: return "no"
    return None

def _choice3(s: str = None):
    s = (s or "").strip().lower()
    if s in {"1", "continue", "next", "c"}: return 1
    if s in {"2", "review", "r"}: return 2
    if s in {"3", "done", "complete", "completed", "finish", "f"}: return 3
    return 0

def build_context(student_inputs: dict) -> str:
    """Shared context appended to AI prompts (always includes student info & problem)."""
    grade = student_inputs.get("get_student_info", "").strip()
    problem = student_inputs.get("get_problem", "").strip()
    parts = ["Context:"]
    if grade:   parts.append(f"- Grade/Course: {grade}")
    if problem: parts.append(f"- Problem: {problem}")
    return "\n".join(parts)

def build_review_message(student_inputs: dict) -> str:
    """A review-focused AI prompt that summarizes progress for a Socratic check."""
    grade = student_inputs.get("get_student_info", "").strip()
    problem = student_inputs.get("get_problem", "").strip()
    concepts = student_inputs.get("concept_review", "").strip()
    work = student_inputs.get("perform_work", "").strip()

    header = (
        "Act as a Socratic tutor. I want to review my work so far and check my reasoning for mistakes, gaps, or "
        "missing justifications. Do NOT give me the final answer. Ask guiding questions and help me verify each step."
    )
    lines = [header, "", "Context & Notes:"]
    if grade:    lines.append(f"- Grade/Course: {grade}")
    if problem:  lines.append(f"- Problem: {problem}")
    if concepts: lines.append(f"- Concepts I identified: {concepts}")
    if work:     lines.append(f"- My current notes/work: {work}")
    lines.append("")
    lines.append("Please:")
    lines.append("1) Ask me to explain my plan or first step.")
    lines.append("2) Probe for units, definitions, and assumptions.")
    lines.append("3) Help me spot any misconceptions or leaps.")
    lines.append("4) If a correction is needed, nudge me to propose it first.")
    return "\n".join(lines)


def copy_button_js(text: str, label="Copy to clipboard"):
    st.code(text, language="markdown")
    if st.button(label, key=f"copy_{hash(text)}"):
        st.session_state["__copy_text__"] = text

    if "__copy_text__" in st.session_state:
        # Use Streamlit's built-in method
        st.markdown(
            f"""
            <textarea id="copyText" style="position: absolute; left: -9999px;">{st.session_state['__copy_text__']}</textarea>
            <script>
                var copyText = document.getElementById("copyText");
                copyText.select();
                document.execCommand("copy");
            </script>
            """,
            unsafe_allow_html=True
        )
        st.success("✓ Copied to clipboard!")
        del st.session_state["__copy_text__"]

def save_to_csv():
    """Append a row snapshot of current session state (lightweight autosave)."""
    row = {
        "session_id": st.session_state.session_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "step_index": st.session_state.current_step_index,
        "step_id": flowchart_steps[st.session_state.current_step_index]["id"],
        "grade_level": st.session_state.student_inputs.get("get_student_info", ""),
        "problem_text": st.session_state.student_inputs.get("get_problem", ""),
        "concepts_reviewed": st.session_state.student_inputs.get("concept_review", ""),
        "knew_first_step": st.session_state.student_inputs.get("first_step_strategy", ""),
        "work_notes": st.session_state.student_inputs.get("perform_work", ""),
        "completion_choice": st.session_state.student_inputs.get("continue_or_complete", "")
    }
    try:
        with open("research_data.csv", "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if f.tell() == 0:
                w.writeheader()
            w.writerow(row)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def download_markdown():
    """Offer a Markdown download of the session notes."""
    md = [
        f"# AI Problem-Solving Session ({st.session_state.session_id})",
        f"**Timestamp:** {datetime.now().isoformat(timespec='seconds')}",
        ""
    ]
    order = [
        "get_student_info", "get_problem", "concept_review",
        "first_step_strategy", "perform_work", "continue_or_complete"
    ]
    labels = {
        "get_student_info": "Grade/Course",
        "get_problem": "Problem",
        "concept_review": "Concepts",
        "first_step_strategy": "Knew first step?",
        "perform_work": "Work notes",
        "continue_or_complete": "Completion choice"
    }
    for k in order:
        v = st.session_state.student_inputs.get(k, "").strip()
        if v:
            md += [f"## {labels[k]}", v, ""]
    st.download_button(
        "⬇️ Download notes (.md)",
        "\n".join(md),
        file_name=f"srl_{st.session_state.session_id}.md"
    )

# -----------------------------
# Streamlit state init
# -----------------------------
st.set_page_config(page_title="SRL AI Tutor Coach", layout="wide")

if "current_step_index" not in st.session_state:
    st.session_state.current_step_index = 0
if "student_inputs" not in st.session_state:
    st.session_state.student_inputs = {}
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "branch_message" not in st.session_state:
    st.session_state.branch_message = None
# NEW: where to jump **after** a branch copy prompt (so review can go to the right place)
if "branch_next_index" not in st.session_state:
    st.session_state.branch_next_index = None
if "completed" not in st.session_state:
    st.session_state.completed = False

# -----------------------------
# Navigation / branching
# -----------------------------
def next_step():
    current_step = flowchart_steps[st.session_state.current_step_index]

    # Persist input if any
    if current_step["input_needed"]:
        user_input = st.session_state.get(f"input_{current_step['id']}", "")
        if user_input is not None:
            st.session_state.student_inputs[current_step["id"]] = user_input

    # Default advance
    next_step_index = st.session_state.current_step_index + 1

    # Branching logic
    if current_step["id"] == "first_step_strategy":
        ans = _yn(st.session_state.student_inputs.get("first_step_strategy"))
        if ans == "yes":
            # Include student info + problem in the AI message
            message = f"{current_step['yes_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.branch_next_index = 5  # go to perform_work after copying
            return
        elif ans == "no":
            message = f"{current_step['no_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.branch_next_index = 5  # go to perform_work after copying
            return
        else:
            st.warning("Please type yes or no (y/n).")
            return

    elif current_step["id"] == "continue_or_complete":
        c = _choice3(st.session_state.student_inputs.get("continue_or_complete"))
        if c == 3:
            # Finish
            save_to_csv()
            st.session_state.completed = True
            st.balloons()
            return
        elif c == 1:
            next_step_index = 4  # first_step_strategy
        elif c == 2:
            # REVIEW PATH: show a purpose-built Socratic review prompt with all context
            review_msg = build_review_message(st.session_state.student_inputs)
            st.session_state.branch_message = review_msg
            st.session_state.branch_next_index = 5  # send to perform_work to capture new notes after review
            return
        else:
            st.warning("Please choose 1 (continue), 2 (review), or 3 (complete).")
            return

    # Commit step change and autosave a snapshot
    if 0 <= next_step_index < len(flowchart_steps):
        st.session_state.current_step_index = next_step_index
        save_to_csv()
    else:
        # graceful finish if we somehow step off the end
        save_to_csv()
        st.session_state.completed = True

# -----------------------------
# UI
# -----------------------------
st.title("SRL AI Tutor Coach")

if st.session_state.completed:
    st.success("🎉 Session completed! Your learning progress has been saved.")
    download_markdown()

    # Add researcher access - NEW CODE
    st.markdown("---")
    st.subheader("Research Data Preview")

    # Add pandas import at the top of your file if not already there
    # Add this with your other imports: import pandas as pd
    try:
        df = pd.read_csv("research_data.csv")
        st.write(f"Total research entries: {len(df)}")

        # Show the last 3 entries from this session
        session_entries = df[df['session_id'] == st.session_state.session_id]
        if not session_entries.empty:
            st.write("**Your session data:**")
            st.dataframe(session_entries)
        else:
            st.info("No data recorded for this session yet")

    except FileNotFoundError:
        st.info("No research data collected yet. The data file will be created after first complete session.")
    except Exception as e:
        st.error(f"Error loading data: {e}")

    st.markdown("---")

    if st.button("Start New Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
else:
    current_step = flowchart_steps[st.session_state.current_step_index]

    # Breadcrumb + progress
    step_names = [s["id"].replace("_", " ").title() for s in flowchart_steps]
    st.caption(" › ".join(step_names[: st.session_state.current_step_index + 1]))
    st.progress((st.session_state.current_step_index + 1) / len(flowchart_steps))
    st.markdown("---")

    # Branch message flow (YES/NO prompts and review)
    if st.session_state.branch_message:
        st.markdown("**Copy this message to your AI:**")
        copy_button_js(st.session_state.branch_message)
        if st.button("✅ I've copied this to the AI"):
            # Jump to the designated next step if provided; otherwise advance by +1
            if isinstance(st.session_state.branch_next_index, int):
                st.session_state.current_step_index = st.session_state.branch_next_index
            else:
                st.session_state.current_step_index += 1
            st.session_state.branch_message = None
            st.session_state.branch_next_index = None
            save_to_csv()
            st.rerun()
    else:
        # Normal step display
        st.markdown(f"### {current_step['prompt']}")

        if current_step["input_needed"]:
            # Use a form to prevent double-reruns and keep inputs stable
            with st.form(key=f"form_{current_step['id']}", clear_on_submit=False):
                st.text_area(
                    "Your response:",
                    key=f"input_{current_step['id']}",
                    height=150,
                    value=st.session_state.student_inputs.get(current_step["id"], "")
                )
                col1, col2 = st.columns([1, 3])
                submitted_next = col1.form_submit_button("Next →")
                submitted_back = col2.form_submit_button("← Back") if st.session_state.current_step_index > 0 else False
            if submitted_next:
                next_step()
                st.rerun()
            if submitted_back:
                st.session_state.current_step_index -= 1
                save_to_csv()
                st.rerun()

        else:
            # Action steps (like prime_ai)
            if current_step["id"] == "prime_ai":
                full_message = (
                    f"{current_step['priming_message']}\n\n"
                    f"{build_context(st.session_state.student_inputs)}"
                )
                st.markdown("**Copy this message to your AI:**")
                copy_button_js(full_message)

            col1, col2 = st.columns([1, 3])
            if col1.button("Next →"):
                next_step()
                st.rerun()
            if st.session_state.current_step_index > 0 and col2.button("← Back"):
                st.session_state.current_step_index -= 1
                save_to_csv()
                st.rerun()

    st.markdown("---")
    download_markdown()

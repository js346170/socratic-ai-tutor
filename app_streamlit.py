# app_streamlit.py
import streamlit as st
import json
import csv
from datetime import datetime
import uuid
import pandas as pd

# Try to import keep_alive (will fail on Streamlit Cloud, but that's okay)
try:
    from keep_alive import start_keep_alive

    start_keep_alive()
except ImportError:
    pass  # This is fine - keep_alive.py won't exist on Streamlit Cloud

# -----------------------------
# Flowchart definition - UPDATED WITH FOLLOW-UP OPTIONS
# -----------------------------
flowchart_steps = [
    {  # Step 0
        "id": "get_student_info",
        "prompt": (
            "Welcome to your Self Reflective Learning Coach. Our goal is to show you an effective method "
            "for using AI for problem solving. Let's get set up. What's your grade level and course? "
            "(e.g., '11th Grade, AP Microeconomics')"
        ),
        "input_needed": True,
        "next_step": "concept_review"
    },
    {  # Step 1 - Concept review comes early
        "id": "concept_review",
        "prompt": (
            "Now let's prepare. Based on your problem, what main concepts do you need to understand?\n\n"
            "Examples:\n- 'Supply and demand curves'\n- 'Price elasticity calculation' \n- 'Deadweight loss formula'\n"
            "- 'Market equilibrium points'\n\n"
            "List any concepts you're unsure about (or type 'none' if you're confident):"
        ),
        "input_needed": True,
        "next_step": "get_problem"
    },
    {  # Step 2 - Get problem after concepts
        "id": "get_problem",
        "prompt": (
            "What specific problem are you working on? Paste it below or if it is a screenshot, paste directly into the AI"
        ),
        "input_needed": True,
        "next_step": "prime_ai"
    },
    {  # Step 3
        "id": "prime_ai",
        "prompt": (
            "CRUCIAL FIRST STEP:\n"
            "1. Open ChatGPT or Claude in your web browser.\n"
            "2. If you have a screenshot of the problem, upload it to the AI first.\n"
            "3. Copy the message below and paste it into the AI.\n"
            "4. Come back here and click 'Next' after you've done this."
        ),
        "input_needed": False,
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
        "next_step": "reflection_and_next_steps",
        "yes_message": (
            "Great! Work with the AI to complete the problem using the Socratic method.\n\n"
            "Copy this to the AI: 'I know the first step. Help me work through this problem step-by-step without giving me the final answer. "
            "Start with the first step. Remember you are scaffolding my learning.'"
        ),
        "no_message": (
            "No problem! Let's get some guidance on where to start.\n\n"
            "Copy this to the AI: 'I don't know where to start. What should be the very first step to solve this problem? Please explain it without "
            "solving the whole thing. Remember, you are scaffolding my learning.'"
        )
    },
    {  # Step 5 - Final step with follow-up options
        "id": "reflection_and_next_steps",
        "prompt": (
            "Great! You've worked with the AI using the Socratic method. \n\n"
            "How did it go with solving the problem?\n\n"
            "- If SUCCESSFUL: Type 'success' for a similar practice problem\n"
            "- If UNSUCCESSFUL: Type 'retry' to get a fresh explanation\n"
            "- If MASTERED: Type 'mastered' if you understand the concept completely"
        ),
        "input_needed": True,
        "next_step": "follow_up_options",
        "success_message": (
            "Excellent! Let's reinforce your learning with a similar practice problem.\n\n"
            "Copy this to the AI: 'Great job helping me learn that concept! "
            "Now please give me a similar practice problem to solve on my own, "
            "but continue acting as a Socratic tutor if I need help.'"
        ),
        "retry_message": (
            "No problem! Let's try a different approach.\n\n"
            "Copy this to the AI: 'I'm still struggling with this concept. "
            "Could you please rephrase your explanation and start from the very beginning? "
            "Use a different teaching approach to help me understand.'"
        ),
        "mastered_message": (
            "Fantastic! You've mastered this concept.\n\n"
            "Copy this to the AI: 'Thank you for your help! I now feel confident that I understand this concept. "
            "I've successfully completed the problem and feel I have mastered the material.'"
        )
    },
    {  # NEW Step 6 - Follow-up options page
        "id": "follow_up_options",
        "prompt": "",
        "input_needed": False,
        "next_step": None
    }
]

# O(1) lookup
STEP_BY_ID = {s["id"]: s for s in flowchart_steps}


def get_step(step_id): return STEP_BY_ID.get(step_id)


# UPDATED FIELDNAMES
FIELDNAMES = [
    "session_id", "timestamp", "step_index", "step_id",
    "grade_level", "problem_text", "concepts_reviewed",
    "knew_first_step", "reflection_response", "successful_learning",
    "follow_up_choice"
]


# -----------------------------
# Helpers
# -----------------------------
def _follow_up(s: str = None):
    s = (s or "").strip().lower()
    if s in {"success", "successful", "s", "1"}: return "success"
    if s in {"retry", "try again", "again", "r", "2"}: return "retry"
    if s in {"mastered", "master", "complete", "m", "3"}: return "mastered"
    return None


def _yn(s: str = None):
    s = (s or "").strip().lower()
    if s in {"y", "yes", "yeah", "yep", "1"}: return "yes"
    if s in {"n", "no", "nope", "0"}: return "no"
    return None


def build_context(student_inputs: dict) -> str:
    """Shared context appended to AI prompts (always includes student info & problem)."""
    grade = student_inputs.get("get_student_info", "").strip()
    problem = student_inputs.get("get_problem", "").strip()
    parts = ["Context:"]
    if grade:   parts.append(f"- Grade/Course: {grade}")
    if problem: parts.append(f"- Problem: {problem}")
    return "\n".join(parts)


def build_priming_message(student_inputs: dict) -> str:
    """Build the AI priming message with student info and concepts"""
    grade = student_inputs.get("get_student_info", "").strip()
    concepts = student_inputs.get("concept_review", "").strip()
    problem = student_inputs.get("get_problem", "").strip()

    base_message = (
        "Please act as a Socratic tutor. I'm a {grade_level} student working on this problem. "
        "I need help with these concepts: {concepts}. "
        "Do not give me the final answer. Help me learn by asking guiding questions, "
        "clarifying concepts, and breaking the problem into smaller steps."
    )

    # Format the message
    message = base_message.format(
        grade_level=grade if grade else "high school",
        concepts=concepts if concepts else "general problem-solving concepts"
    )

    # Add the problem if available
    if problem:
        message += f"\n\nHere's the problem I'm working on:\n{problem}"

    message += "\n\nLet's review the concepts before getting into the problem."

    return message


def copy_button_js(text: str):
    # Simple, reliable approach - just show the text with copy instructions
    st.code(text, language="markdown")
    st.caption("📋 Use the copy button in the top-right corner of the code block above")


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
        "reflection_response": st.session_state.student_inputs.get("reflection_and_next_steps", ""),
        "successful_learning": _follow_up(st.session_state.student_inputs.get("reflection_and_next_steps", "")),
        "follow_up_choice": st.session_state.get("follow_up_choice", "")
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
        "get_student_info", "concept_review", "get_problem",
        "first_step_strategy", "reflection_and_next_steps"
    ]
    labels = {
        "get_student_info": "Grade/Course",
        "concept_review": "Concepts",
        "get_problem": "Problem",
        "first_step_strategy": "Knew first step?",
        "reflection_and_next_steps": "Learning outcome"
    }
    for k in order:
        v = st.session_state.student_inputs.get(k, "").strip()
        if v:
            md += [f"## {labels[k]}", v, ""]

    if "follow_up_choice" in st.session_state:
        md += ["## Follow-up Choice", st.session_state.follow_up_choice, ""]

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
if "branch_next_index" not in st.session_state:
    st.session_state.branch_next_index = None
if "completed" not in st.session_state:
    st.session_state.completed = False
if "follow_up_choice" not in st.session_state:
    st.session_state.follow_up_choice = ""


# -----------------------------
# Navigation / branching - UPDATED WITH FOLLOW-UP
# -----------------------------
def next_step():
    current_step = flowchart_steps[st.session_state.current_step_index]

    # Persist input if any
    if current_step["input_needed"]:
        user_input = st.session_state.get(f"input_{current_step['id']}", "")
        if user_input is not None:
            st.session_state.student_inputs[current_step["id"]] = user_input

    # Handle branching steps
    if current_step["id"] == "first_step_strategy":
        ans = _yn(st.session_state.student_inputs.get("first_step_strategy"))
        if ans == "yes":
            message = f"{current_step['yes_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.branch_next_index = 5  # reflection_and_next_steps
            st.session_state.current_step_index += 1
            return
        elif ans == "no":
            message = f"{current_step['no_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.branch_next_index = 5  # reflection_and_next_steps
            st.session_state.current_step_index += 1
            return
        else:
            st.warning("Please type yes or no (y/n).")
            return

    elif current_step["id"] == "reflection_and_next_steps":
        ans = _follow_up(st.session_state.student_inputs.get("reflection_and_next_steps"))
        if ans == "success":
            message = f"{current_step['success_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.follow_up_choice = "requested_similar_problem"
            st.session_state.branch_next_index = 6  # follow_up_options
            return
        elif ans == "retry":
            message = f"{current_step['retry_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.follow_up_choice = "requested_rephrasing"
            st.session_state.branch_next_index = 6  # follow_up_options
            return
        elif ans == "mastered":
            message = f"{current_step['mastered_message']}\n\n{build_context(st.session_state.student_inputs)}"
            st.session_state.branch_message = message
            st.session_state.follow_up_choice = "concept_mastered"
            st.session_state.branch_next_index = 6  # follow_up_options
            return
        else:
            st.warning("Please type 'success', 'retry', or 'mastered'.")
            return

    # Default linear progression
    next_step_index = st.session_state.current_step_index + 1

    if 0 <= next_step_index < len(flowchart_steps):
        st.session_state.current_step_index = next_step_index
        save_to_csv()
    else:
        save_to_csv()
        st.session_state.completed = True


# -----------------------------
# UI - WITH COMPREHENSIVE FOLLOW-UP OPTIONS
# -----------------------------
st.title("SRL AI Tutor Coach")

if st.session_state.completed:
    st.success("🎉 Session completed! Your learning progress has been saved.")
    download_markdown()

    # Add researcher access
    st.markdown("---")
    st.subheader("Research Data Preview")

    try:
        df = pd.read_csv("research_data.csv")
        st.write(f"Total research entries: {len(df)}")

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

elif st.session_state.current_step_index == 6:  # Follow-up options page
    st.success("🎯 Great job completing the AI learning process!")

    st.markdown("### 📝 How to Use AI Effectively on Your Own")
    st.markdown("""
    **Remember these steps when using AI for learning:**

    1. **Prime the AI** - Always start with: "Please act as a Socratic tutor. Help me learn by asking guiding questions rather than giving direct answers."
    2. **Provide context** - Share your grade level, course, and what concepts you're struggling with
    3. **Be specific** - Paste the exact problem you're working on
    4. **Ask for step-by-step** - Request scaffolding, not just the final answer
    5. **Review concepts first** - Ask the AI to help you understand the underlying concepts before solving
    6. **Request similar problems** - Once you understand, ask for practice problems to reinforce learning
    """)

    st.markdown("---")
    st.markdown("### 🎯 Your AI Message Ready to Copy:")
    copy_button_js(st.session_state.branch_message)

    st.markdown("---")
    st.markdown("### 🔄 What would you like to do next?")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Work with AI & Continue", type="primary"):
            st.session_state.branch_message = None
            st.info("✅ Message copied! Work with the AI and you can come back anytime.")

    with col2:
        if st.button("🏁 Complete Session"):
            save_to_csv()
            st.session_state.completed = True
            st.rerun()

    with col3:
        if st.button("↺ Start New Session"):
            for key in list(st.session_state.keys()):
                if key not in ['session_id']:
                    del st.session_state[key]
            st.session_state.current_step_index = 0
            st.session_state.student_inputs = {}
            st.rerun()

else:
    current_step = flowchart_steps[st.session_state.current_step_index]

    # Breadcrumb + progress
    step_names = [s["id"].replace("_", " ").title() for s in flowchart_steps]
    st.caption(" › ".join(step_names[: st.session_state.current_step_index + 1]))
    st.progress((st.session_state.current_step_index + 1) / len(flowchart_steps))

    # Single Back to Beginning button at the top
    if st.session_state.current_step_index > 0:
        if st.button("↺ Back to Beginning", key="back_to_start_top"):
            for key in list(st.session_state.keys()):
                if key not in ['session_id']:
                    del st.session_state[key]
            st.session_state.current_step_index = 0
            st.session_state.student_inputs = {}
            st.rerun()

    st.markdown("---")

    # Branch message flow
    if st.session_state.branch_message:
        st.markdown("**Here's your message for the AI:**")
        copy_button_js(st.session_state.branch_message)

        if st.button("✅ I've copied this to the AI"):
            if isinstance(st.session_state.branch_next_index, int):
                st.session_state.current_step_index = st.session_state.branch_next_index
            st.session_state.branch_message = None
            st.session_state.branch_next_index = None
            save_to_csv()
            st.rerun()

    else:
        # Normal step display
        st.markdown(f"### {current_step['prompt']}")

        if current_step["input_needed"]:
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
            if current_step["id"] == "prime_ai":
                full_message = build_priming_message(st.session_state.student_inputs)
                st.markdown("**Here's your message for the AI:**")
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
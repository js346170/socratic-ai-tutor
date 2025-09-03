# src/models/flowchart.py

flowchart_steps = [
    {   # Step 0
        "id": "get_student_info",
        "prompt": "Welcome to your Self Reflective Learning Coach. Our goal is to show you an effective method for using AI for problem solving. For now, follow our programs prompts, in the future you can do this without our help! Let's get set up. What's your grade level and course? (e.g., '11th Grade, AP Microeconomics')",
        "input_needed": True,
        "next_step": "get_problem"
    },
    {   # Step 1
        "id": "get_problem",
        "prompt": "What specific problem are you working on? Paste it below or if it is a screenshot, paste directly into the AI",
        "input_needed": True,
        "next_step": "prime_ai"
    },
    {    # Step 2
        "id": "prime_ai",
        "prompt": "CRUCIAL FIRST STEP:\n1. Open ChatGPT or Claude in your web browser.\n2. If you have a screenshot of the problem, upload it to the AI first.\n3. Copy the message below and paste it into the AI.\n4. Come back here and click 'Next' after you've done this.",
        "input_needed": False,
        "next_step": "concept_review",
        "priming_message": "Please act as a Socratic tutor. I've provided the problem above. Do not give me the final answer. Help me learn by asking guiding questions, clarifying concepts, and breaking the problem into smaller steps."
    },
{   # Step 3 - NEW
        "id": "concept_review",
        "prompt": "Now let's prepare. Based on your problem, what main concepts do you need to understand?\n\nExamples:\n- 'Supply and demand curves'\n- 'Price elasticity calculation' \n- 'Deadweight loss formula'\n- 'Market equilibrium points'\n\nList any concepts you're unsure about (or type 'none' if you're confident):",
        "input_needed": True,
        "next_step": "first_step_strategy"
    },
    {  # Step 4 - REVISED with your smart branching
        "id": "first_step_strategy",  # Changed from "identify_first_step"
        "prompt": "Do you know what the FIRST STEP should be to solve this problem?\n\n- If YES: Type 'yes' and we'll help you work through it step-by-step\n- If NO: Type 'no' and we'll ask the AI for just the first step",
        "input_needed": True,
        "next_step": "perform_work",
        "yes_message": "Great! Work with the AI to complete as much as you can. When you get stuck, come back and tell me where you need help.\n\nCopy this to the AI: 'Help me work through this problem step-by-step without giving me the final answer. Start with the first step. Remember you are scaffolding my learning'",
        "no_message": "No problem! Let's get some guidance on where to start.\n\nCopy this to the AI: 'What should be the very first step to solve this problem? Please explain it without solving the whole thing. Remember, you are scaffolding my learning'"
    },
    {  # Step 5 - NEW
        "id": "perform_work",  # Changed from "perform_step" to match branching logic
        "prompt": "Now work on that first step with the AI's help. When you're ready, come back and tell me what you did or what you learned:",
        "input_needed": True,
        "next_step": "continue_or_complete"
    },
    {   # Step 6 - NEW
        "id": "continue_or_complete",
        "prompt": "Great progress! Do you want to:\n1. Continue to the next step\n2. Review your work so far\n3. You've completed the problem",
        "input_needed": True,
        "next_step": None  # This will need special handling
    }
]

def get_step(step_id):
    """Find a step by its ID"""
    for step in flowchart_steps:
        if step["id"] == step_id:
            return step
    return None


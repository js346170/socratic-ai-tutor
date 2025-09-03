# src/app_streamlit.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from models.flowchart import flowchart_steps, get_step  # Add get_step to the import


class SRLCoachApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SRL AI Tutor Coach")
        self.root.geometry("800x600")

        # Track the current state
        self.current_step_index = 0  # Start at the first step
        self.current_step = flowchart_steps[self.current_step_index]
        self.student_inputs = {}  # To store all user answers

        # Create the UI
        self.create_widgets()

        # Load the first step
        self.load_step(self.current_step)

    def create_widgets(self):
        """Create all the UI elements"""
        # Main instruction label
        self.instruction_label = ttk.Label(self.root, text="", wraplength=700)
        self.instruction_label.pack(pady=20)

        # Add a special frame for the AI priming message (will be hidden most of the time)
        self.message_frame = ttk.Frame(self.root)
        self.message_label = ttk.Label(self.message_frame, text="", wraplength=700, background="light yellow",
                                       padding=10)
        self.message_label.pack()
        self.message_frame.pack_forget()  # Start hidden

        # Add copy button (will be hidden most of the time)
        self.copy_button = ttk.Button(self.root, text="📋 Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack_forget()  # Start hidden

        # Frame for user input
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10, fill="x")

        self.user_input_entry = scrolledtext.ScrolledText(input_frame, height=4, width=80)
        self.user_input_entry.pack()

        # Frame for buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)

        self.back_button = ttk.Button(button_frame, text="< Back", command=self.previous_step)
        self.back_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(button_frame, text="Next >", command=self.next_step)
        self.next_button.pack(side=tk.LEFT, padx=5)

    def load_step(self, step):
        """Load and display a step from the flowchart"""
        # Display the prompt for the current step
        self.instruction_label.config(text=step["prompt"])

        # Clear the input field
        self.user_input_entry.delete(1.0, tk.END)

        # Show or hide elements based on the step type
        if step["id"] == "prime_ai":
            # For the AI priming step: show message and copy button, hide input
            problem_text = self.student_inputs.get("get_problem", "")
            full_message = f"{step['priming_message']}\n\n{problem_text}"
            self.message_label.config(text=full_message)
            self.message_frame.pack()
            self.copy_button.pack()
            self.user_input_entry.pack_forget()  # This hides the input for prime_ai

        elif step["id"] == "first_step_strategy":
            # For the strategy step, show input field, hide message and copy button
            self.user_input_entry.pack()
            self.message_frame.pack_forget()
            self.copy_button.pack_forget()

        else:
            # For other steps: hide message and copy button, show input if needed
            self.message_frame.pack_forget()
            self.copy_button.pack_forget()
            if step["input_needed"]:
                self.user_input_entry.pack()  # Show input for steps that need it
            else:
                self.user_input_entry.pack_forget()  # Hide input for steps that don't need it

    def next_step(self):
        """Move to the next step in the flowchart with branching logic"""
        # Save the user's input for the current step
        if self.current_step["input_needed"]:
            user_text = self.user_input_entry.get(1.0, tk.END).strip().lower()
            self.student_inputs[self.current_step["id"]] = user_text
            print(f"Saving: {user_text}")

        # Handle special branching logic
        next_step_id = self.current_step["next_step"]

        if self.current_step["id"] == "first_step_strategy":
            user_response = self.student_inputs.get("first_step_strategy", "")
            if user_response == "yes":
                next_step_id = "perform_work"
                self.show_branch_message(self.current_step["yes_message"])
                return
            elif user_response == "no":
                next_step_id = "perform_work"
                self.show_branch_message(self.current_step["no_message"])
                return
            else:
                self.instruction_label.config(text="Please type 'yes' or 'no' to continue.")
                return

            # === Branch 2: continue_or_complete ===
        if self.current_step["id"] == "continue_or_complete":
            choice = self.student_inputs.get("continue_or_complete", "").strip()
            if choice in ("1", "continue", "next"):
                next_step_id = "first_step_strategy"  # loop again
            elif choice in ("2", "review"):
                next_step_id = "concept_review"  # send back to review
            elif choice in ("3", "done", "complete", "completed"):
                from tkinter import messagebox
                messagebox.showinfo("All set!", "Nice work—flow complete. Save your notes!")
                self.root.destroy()
                return
            else:
                self.instruction_label.config(text="Please type 1, 2, or 3.")
                return

            # === Generic fallback ===
        next_step_obj = get_step(next_step_id)
        if next_step_obj:
            self.current_step_index = self.find_step_index(next_step_id)
            self.current_step = next_step_obj
            self.load_step(self.current_step)
        else:
            print("End of flowchart reached!")

    # Helper function to find a step's index by ID
    def find_step_index(self, step_id):
        for i, step in enumerate(flowchart_steps):
            if step["id"] == step_id:
                return i
        return 0

    def previous_step(self):
        """Move to the previous step in the flowchart"""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.current_step = flowchart_steps[self.current_step_index]
            self.load_step(self.current_step)

    def show_branch_message(self, message):
        """Show a message with copy functionality for branch steps"""
        # Update the message label with the branch-specific message
        self.message_label.config(text=message)

        # Show the message frame and copy button
        self.message_frame.pack()
        self.copy_button.pack()

        # Hide the input field since we're showing a message to copy
        self.user_input_entry.pack_forget()

        # Update the instruction to tell them what to do next
        self.instruction_label.config(text="Copy the message above to the AI, then click 'Next' to continue.")

    def copy_to_clipboard(self):
        """Copy the visible guidance message to clipboard"""
        try:
            import pyperclip
            text_to_copy = self.message_label.cget("text")
            if not text_to_copy:
                # fall back to priming_message + problem if available
                problem_text = self.student_inputs.get("get_problem", "")
                text_to_copy = f"{self.current_step.get('priming_message', '').strip()} {problem_text}".strip()
            pyperclip.copy(text_to_copy)
            print("✅ Message copied to clipboard!")
        except ImportError:
            print("❌ Pyperclip not available")


# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = SRLCoachApp(root)
    root.mainloop()
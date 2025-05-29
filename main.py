import tkinter as tk
from tkinter import scrolledtext, Listbox, END, messagebox, Toplevel
from tkinter import ttk  # For Combobox
import re
import pyperclip  # Requires installation: pip install pyperclip
import time # To help manage update frequency if needed (optional)

# --- Tooltip Class (Unchanged) ---
class ToolTip:
    """
    Create a tooltip for a given widget.
    """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self._id = None # To store after() id
        self._scheduled = False # Flag to check if already scheduled
        widget.bind("<Enter>", self.schedule_tooltip)
        widget.bind("<Leave>", self.leave)
        widget.bind("<ButtonPress>", self.leave) # Hide on click too

    def schedule_tooltip(self, event=None):
        # Schedule tooltip appearance after a short delay (e.g., 500ms)
        if not self._scheduled:
             self._scheduled = True
             self._id = self.widget.after(500, self.enter)

    def enter(self, event=None):
        self._scheduled = False # Reset scheduled flag
        # If the cursor is still over the widget
        if self.widget.winfo_containing(self.widget.winfo_pointerx(), self.widget.winfo_pointery()) == self.widget:
            x, y, _, _ = self.widget.bbox("insert") # Get position relative to widget
            # Adjust position if bbox is not available (e.g., for listbox items)
            if x is None or y is None:
                 x = event.x if event else 0
                 y = event.y if event else 0

            x += self.widget.winfo_rootx() + 20 # Offset from cursor
            y += self.widget.winfo_rooty() + 20

            # Creates a toplevel window
            self.tooltip_window = Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True) # No window decorations
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

            label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                             background='#FFFFE0', relief='solid', borderwidth=1, # Light yellow background
                             wraplength=350, # Wrap text if too long
                             font=("Arial", 9, "normal"))
            label.pack(ipadx=2, ipady=2)

    def leave(self, event=None):
        # Cancel scheduled tooltip if leaving before it appears
        if self._id:
             self.widget.after_cancel(self._id)
             self._id = None
             self._scheduled = False
        # Destroy existing tooltip window
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

# --- Data Extracted and Enhanced (Added 'name' field) ---

PROMPT_ELEMENTS = {
    # Name: {color, keywords_regex}
    "Instruction": {"color": "#ADD8E6", "keywords_regex": r'(?i)\b(summarize|translate|write|explain|list|create|generate|classify|analyze|compare|define|calculate|tell me|what is|how does|why is|act as|provide|describe|identify)\b'},
    "Context": {"color": "#90EE90", "keywords_regex": r'(?i)\b(given the context|based on this text|considering the following|with this information|background:|scenario:|context:)\b'},
    "Input Data": {"color": "#FFFACD", "keywords_regex": r'(?i)\b(input:|data:|text:|article:|example:|document:|user query:|information:)\b'},
    "Output Format": {"color": "#FFB6C1", "keywords_regex": r'(?i)\b(format as|output in|use bullet points|provide a json|return a list|in xml|step-by-step|in markdown|as a table|limit to|maximum|minimum)\b'},
    "Role": {"color": "#E6E6FA", "keywords_regex": r'(?i)\b(you are a|act as a|your role is|assume the persona of)\b'},
    "Delimiter": {"color": "#FFA07A", "keywords_regex": r'(###|---|"""|```|<[a-zA-Z_]+>|##)'}, # More generic tag pattern
    "Example Marker": {"color": "#DAA520", "keywords_regex": r'(?i)\b(example \d+:|example:|e\.g\.:)\b'}, # Highlight examples
    "CoT Trigger": {"color": "#FFDAB9", "keywords_regex": r'(?i)\b(let\'?s think step-by-step|think step by step|step-by-step reasoning)\b'}, # Highlight CoT triggers
}

PROMPT_TECHNIQUES_DATA = {
    # Technique Name: {name, description, use_case, template}
    "Zero-shot": {
        "name": "Zero-shot",
        "description": "Direct instruction without examples.",
        "use_case": "Good for general tasks the LLM understands well (e.g., summarization, translation, simple Q&A).",
        "template": "Instruction: [Clearly state the task, e.g., Summarize the following text]\n\nInput Data: [Provide the necessary information/text here]"
    },
    "Few-shot": {
        "name": "Few-shot",
        "description": "Provide 2-5 examples to show the pattern.",
        "use_case": "Helps the LLM learn input-output patterns for specific or nuanced tasks (e.g., custom classification, style imitation, data formatting).",
        "template": "Instruction: [State the task, e.g., Classify the sentiment of the sentence]\n\nExample 1:\nInput: [Example Input 1]\nOutput: [Example Output 1]\n\nExample 2:\nInput: [Example Input 2]\nOutput: [Example Output 2]\n\n---\n\nActual Input:\nInput Data: [Provide the actual input for the task]"
    },
    "CoT (Chain of Thought)": {
        "name": "CoT (Chain of Thought)",
        "description": "Encourage step-by-step reasoning.",
        "use_case": "Useful for math problems, logic puzzles, multi-step reasoning, and explaining complex processes.",
        "template": "Instruction: [State the problem/question, e.g., What is 5 * (3 + 2)?]\n\nLet's think step-by-step:"
    },
    "Self-consistency": {
        "name": "Self-consistency",
        "description": "Generate multiple reasoning paths, choose best.",
        "use_case": "Increases reliability for arithmetic, commonsense, and symbolic reasoning tasks by sampling diverse reasoning paths.",
        "template": "Instruction: [State the problem, e.g., Solve this riddle...]\n\nThink step-by-step through multiple possible reasoning paths and select the most consistent answer."
    },
    "Generate Knowledge": {
        "name": "Generate Knowledge",
        "description": "Prompt model to recall knowledge first.",
        "use_case": "Useful for questions requiring factual recall or building upon existing knowledge before answering.",
        "template": "Question: [Your main question]\n\nFirst, generate some background knowledge about [Topic related to the question].\n\nUsing that knowledge, answer the original question."
    },
    "Prompt Chaining": {
        "name": "Prompt Chaining",
        "description": "Break complex tasks into sequential prompts.",
        "use_case": "Manages complexity, improves debuggability, allows human intervention in multi-step workflows (e.g., extract data -> analyze data -> summarize findings).",
        "template": "# Task: [Overall Goal]\n\nStep 1 Prompt:\nInstruction: [Instruction for the first sub-task]\nInput: [Input for Step 1]\n\n---\n\nStep 2 Prompt (uses output from Step 1):\nInstruction: [Instruction for the second sub-task]\nInput: [Output from Step 1]\n\n# (Continue as needed)"
    },
    "Tree of Thoughts": {
        "name": "Tree of Thoughts",
        "description": "Explore multiple reasoning paths like a tree.",
        "use_case": "Advanced technique for complex problem-solving where multiple possibilities need evaluation (e.g., planning, strategic games).",
        "template": "Problem: [Describe the complex problem]\n\nExplore multiple potential solution paths or reasoning steps. Evaluate each path's viability. Select the most promising path or synthesize the best elements.\nConsider these initial branches:\n1. [Branch 1 Idea]\n2. [Branch 2 Idea]\n..."
    },
    "RAG (Retrieval-Augmented Generation)": {
        "name": "RAG (Retrieval-Augmented Generation)",
        "description": "Integrate external knowledge.",
        "use_case": "Improves accuracy and reduces hallucination for questions based on specific documents, databases, or recent information.",
        "template": "Context retrieved from [Source Name, e.g., Document X]:\n\"\"\"\n[Paste relevant context/text snippet here]\n\"\"\"\n\nBased *only* on the provided context, answer the following question:\nQuestion: [Your question about the context]"
    },
    "Directional Stimulus": {
        "name": "Directional Stimulus",
        "description": "Steer thinking style with a phrase.",
        "use_case": "Controls the tone, complexity, persona, or perspective of the response (e.g., 'Explain like I'm five', 'Write in a formal tone', 'Respond as a pirate').",
        "template": "[Guiding Phrase: e.g., Explain like I'm five / Write in the style of Shakespeare / Act as a helpful assistant]: [Your core instruction or question]"
    },
    "PAL (Program-Aided Language Models)": {
        "name": "PAL (Program-Aided Language Models)",
        "description": "Ask model to write/execute code.",
        "use_case": "Enhances logic and mathematical accuracy for problems solvable with code (e.g., complex calculations, data manipulation).",
        "template": "Instruction: [Describe the problem clearly, e.g., Calculate the standard deviation of these numbers: 5, 8, 12, 15]\n\nWrite [Language, e.g., Python] code to solve this. Show the code, then execute it and provide the final numerical answer."
    },
    "ReAct (Reason and Act)": {
        "name": "ReAct (Reason and Act)",
        "description": "Combine reasoning and tool use in a loop.",
        "use_case": "Enables agents to perform dynamic multi-step tasks involving external tools (search, calculators, APIs) by reasoning, acting, and observing.",
        "template": "Goal: [State the overall objective, e.g., Find the current weather in London and the capital of France]\n\nThought: I need to find the weather in London first. I can use a search tool.\nAction: Search('current weather in London')\nObservation: [Result from search, e.g., 15°C, cloudy]\nThought: Now I need the capital of France. I can use search again.\nAction: Search('capital of France')\nObservation: [Result from search, e.g., Paris]\nThought: I have both pieces of information.\nFinal Answer: The current weather in London is 15°C and cloudy. The capital of France is Paris."
    },
     "Meta Prompting": {
        "name": "Meta Prompting",
        "description": "Ask the model to help create/refine prompts.",
        "use_case": "Useful for generating prompt ideas, improving existing prompts, or selecting the best prompt for a task.",
        "template": "Task: [Describe the task you want a prompt for, e.g., Summarize scientific papers]\n\nGenerate 3 effective prompts an LLM could use to accomplish this task. Explain why each prompt is good."
     },
     "Graph Prompting": {
        "name": "Graph Prompting",
        "description": "Use graph structures for logic/relationships.",
        "use_case": "Excellent for reasoning about relationships, dependencies, or paths in structured data (e.g., social networks, flowcharts, knowledge graphs).",
        "template": "Consider the following relationships represented as a graph:\nNodes: [List nodes, e.g., A, B, C, D]\nEdges: [List connections, e.g., A -> B, B -> C, A -> D]\n\nQuestion: [Ask a question about the graph, e.g., What is the shortest path from A to C?]"
     }
    # Add more techniques from the document as needed
}

GENERAL_TIPS = {
    "Be Specific": "Clearly define the task, desired output, and any constraints. Avoid ambiguity.",
    "Use Action Verbs": "Start instructions with clear verbs like 'Summarize', 'Generate', 'Translate', 'Analyze'.",
    "Structure Input/Output": "Use delimiters (###, ```), Markdown, JSON, or XML for clarity, especially with complex inputs or multiple parts.",
    "Provide Context": "Give necessary background information, especially if the task requires domain knowledge or specific scenario understanding.",
    "Avoid Negations": "Instead of 'Don't use jargon', say 'Explain in simple terms'. State the desired outcome positively.",
    "Break Down Tasks": "For complex goals, use Prompt Chaining or outline steps clearly within a single prompt.",
    "Consider Role Playing": "Use 'Act as a...' (Role element) to set a persona or expertise level (Directional Stimulus).",
    "Specify Constraints": "Define length limits, tone, style, or information to include/exclude (Output Format).",
    "Iterate and Refine": "Prompting is often iterative; test results and adjust your prompt based on the output.",
}

# --- Application Class ---

class PromptBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Prompt Builder & Analyzer (v3)")
        self.root.geometry("1000x800") # Increased size further

        self._analysis_job = None # To store the 'after' job ID for debouncing analysis

        # --- Top Frame for Template Selection ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=(10, 5), padx=10, fill=tk.X)

        tk.Label(top_frame, text="Load Template:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 5))

        self.template_var = tk.StringVar()
        self.template_options = ["Select a Template..."] + list(PROMPT_TECHNIQUES_DATA.keys())
        self.template_combo = ttk.Combobox(top_frame, textvariable=self.template_var,
                                           values=self.template_options, state="readonly", width=30)
        self.template_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.template_combo.current(0)
        self.template_combo.bind("<<ComboboxSelected>>", self.load_template)

        # Tooltip for the Combobox
        self.template_tooltip = ToolTip(self.template_combo, "")
        # No need to bind <Enter> here, tooltip text updates when selection changes or on load_template

        # --- Main Paned Window ---
        paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=5, background="#f0f0f0")
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # --- Input Area Frame ---
        input_frame = tk.Frame(paned_window, bd=1, relief=tk.SUNKEN)
        tk.Label(input_frame, text="Enter or Modify Prompt Here:", font=("Arial", 12, "bold")).pack(pady=(5,2), anchor=tk.W, padx=5)
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=15, width=100, font=("Arial", 10), undo=True, relief=tk.FLAT, borderwidth=0)
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.input_text.bind("<KeyRelease>", self.schedule_analysis) # Schedule analysis on key release
        paned_window.add(input_frame, minsize=100) # Add minimum size

        # --- Analysis and Suggestions Frame (Horizontal Paned Window) ---
        analysis_suggestions_pane = tk.PanedWindow(paned_window, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5, background="#f0f0f0")

        # --- Analysis Area Frame ---
        analysis_frame = tk.Frame(analysis_suggestions_pane, bd=1, relief=tk.SUNKEN)
        tk.Label(analysis_frame, text="Analysis (Highlighted):", font=("Arial", 12, "bold")).pack(pady=(5,2), anchor=tk.W, padx=5)
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD, height=15, width=60, state=tk.DISABLED, font=("Arial", 10), relief=tk.FLAT, borderwidth=0)
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        # Configure tags for highlighting
        for element, config in PROMPT_ELEMENTS.items():
            self.analysis_text.tag_configure(element, background=config["color"], font=("Arial", 10, "bold"))
        analysis_suggestions_pane.add(analysis_frame, minsize=200)

        # --- Suggestions Area Frame ---
        suggestions_frame = tk.Frame(analysis_suggestions_pane, bd=1, relief=tk.SUNKEN)
        tk.Label(suggestions_frame, text="Suggestions & Techniques:", font=("Arial", 12, "bold")).pack(pady=(5,2), anchor=tk.W, padx=5)
        self.suggestions_list = Listbox(suggestions_frame, height=15, width=50, font=("Arial", 9), relief=tk.FLAT, borderwidth=0)
        self.suggestions_list.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.suggestions_list.bind("<Motion>", self.update_suggestion_tooltip)
        self.suggestions_list.bind("<Double-Button-1>", self.show_suggestion_detail)
        self.suggestion_tooltip = ToolTip(self.suggestions_list, "")
        analysis_suggestions_pane.add(suggestions_frame, minsize=200)

        paned_window.add(analysis_suggestions_pane, minsize=150)


        # --- Bottom Frame for Copy Button ---
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=(5, 10))
        self.copy_button = tk.Button(bottom_frame, text="Copy Input Prompt", command=self.copy_to_clipboard, font=("Arial", 10))
        self.copy_button.pack()

        # Initial analysis
        self.analyze_prompt() # Perform initial analysis

    def schedule_analysis(self, event=None):
        """Schedules the analysis to run after a short delay to avoid running on every keystroke."""
        # Cancel the previous job, if any
        if self._analysis_job:
            self.root.after_cancel(self._analysis_job)

        # Schedule the new job
        self._analysis_job = self.root.after(350, self.analyze_prompt) # Delay in milliseconds

    def update_combobox_tooltip(self):
        """Update tooltip text for the combobox based on selection."""
        selected_template = self.template_var.get()
        if selected_template != "Select a Template..." and selected_template in PROMPT_TECHNIQUES_DATA:
            data = PROMPT_TECHNIQUES_DATA[selected_template]
            # Include technique name in Use Case description
            tooltip_text = f"Technique: {data['name']}\n\n{data['description']}\n\nUse Case ({data['name']}): {data['use_case']}"
            self.template_tooltip.text = tooltip_text
        else:
            self.template_tooltip.text = "Select a technique template from the dropdown."

    def load_template(self, event=None):
        """Loads the selected template into the input text area."""
        selected_template = self.template_var.get()
        if selected_template != "Select a Template..." and selected_template in PROMPT_TECHNIQUES_DATA:
            template_text = PROMPT_TECHNIQUES_DATA[selected_template]["template"]
            if self.input_text.get("1.0", tk.END).strip():
                 if not messagebox.askyesno("Confirm Load", "Loading a template will replace the current text in the input area. Continue?"):
                     self.template_var.set("Select a Template...")
                     self.update_combobox_tooltip() # Update tooltip after reset
                     return

            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", template_text)
            self.update_combobox_tooltip() # Update tooltip after load
            self.analyze_prompt() # Re-analyze after loading

    def analyze_prompt(self):
        """Analyzes the input text, highlights elements, and updates suggestions."""
        prompt = self.input_text.get("1.0", tk.END).strip()
        self.analysis_text.config(state=tk.NORMAL)
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert("1.0", prompt)

        # --- Highlighting ---
        found_elements = set()
        analysis_details = {"length": len(prompt.split())} # Store analysis details

        for element, config in PROMPT_ELEMENTS.items():
            try:
                # Find all matches for the element's regex pattern
                for match in re.finditer(config["keywords_regex"], prompt):
                    start_index = f"1.0+{match.start()}c"
                    end_index = f"1.0+{match.end()}c"
                    self.analysis_text.tag_add(element, start_index, end_index)
                    found_elements.add(element)
                    # Store counts for specific structural elements
                    if element == "Example Marker":
                        analysis_details["examples_found"] = analysis_details.get("examples_found", 0) + 1
                    if element == "CoT Trigger":
                         analysis_details["cot_trigger_found"] = True

            except re.error as e:
                print(f"Regex error for element '{element}': {e}") # Debugging

        # --- Structural Pattern Checks (More Thorough Analysis) ---
        prompt_lower = prompt.lower()
        # Check for RAG-like structure (Context + Question)
        if re.search(r'(?i)\b(context:|based on)\b.*\b(question:|what is|how does)\b', prompt, re.DOTALL):
             analysis_details["rag_structure_detected"] = True
        # Check for potential Few-shot structure (multiple examples)
        if analysis_details.get("examples_found", 0) >= 2:
             analysis_details["few_shot_structure_detected"] = True
        # Check for CoT structure
        if analysis_details.get("cot_trigger_found", False):
             analysis_details["cot_structure_detected"] = True


        self.analysis_text.config(state=tk.DISABLED)

        # Update suggestions based on analysis details
        self.update_suggestions(prompt, found_elements, analysis_details)

    def update_suggestions(self, prompt, found_elements, analysis_details):
        """Populates the suggestions list based on the prompt content and analysis."""
        self.suggestions_list.delete(0, END)
        suggestions_data = {} # Store text -> full data mapping for tooltips

        # --- Add Specific Feedback Based on Analysis ---
        if not prompt:
            suggestion_text = "[INFO] Start by typing or loading a template."
            self.suggestions_list.insert(END, suggestion_text)
            suggestions_data[suggestion_text] = "The input area is empty. Type your prompt or select a template from the dropdown above."
            self.suggestions_data = suggestions_data # Store data for tooltips
            return # Stop here if prompt is empty

        # Instruction Check
        if "Instruction" not in found_elements:
            suggestion_text = "[!] Add Clear Instruction"
            self.suggestions_list.insert(END, suggestion_text)
            suggestions_data[suggestion_text] = "Missing Instruction:\n\nClearly state the main task using action verbs (e.g., 'Summarize', 'Explain', 'Generate'). This is crucial for the LLM to understand the goal."

        # Detail/Length Check
        if analysis_details["length"] < 10 and not analysis_details.get("few_shot_structure_detected"):
             suggestion_text = "[TIP] Consider More Detail/Context"
             self.suggestions_list.insert(END, suggestion_text)
             suggestions_data[suggestion_text] = "Brief Prompt:\n\nIf the task is complex or requires specific background, consider adding more context, details, constraints, or examples."

        # Negation Check
        if re.search(r'\b(not|don\'t|never|avoid|without)\b', prompt, re.IGNORECASE):
             suggestion_text = "[TIP] Rephrase Negations Positively"
             self.suggestions_list.insert(END, suggestion_text)
             suggestions_data[suggestion_text] = "Avoid Negations:\n\nInstead of saying what *not* to do (e.g., 'don't be vague'), state the desired outcome positively (e.g., 'be specific and detailed'). This is usually clearer for the LLM."

        # Output Format Check
        if "Output Format" not in found_elements and analysis_details["length"] > 20: # Suggest if reasonably long
             suggestion_text = "[TIP] Specify Output Format?"
             self.suggestions_list.insert(END, suggestion_text)
             suggestions_data[suggestion_text] = "Consider Output Format:\n\nFor clearer results, especially with complex outputs, explicitly state the desired format (e.g., 'Format as a JSON object with keys X and Y', 'Use bullet points for the main ideas', 'Create a markdown table with columns A, B, C')."

        # Structure Check (Delimiters)
        if "Delimiter" not in found_elements and analysis_details["length"] > 30 and (analysis_details.get("examples_found", 0) > 0 or "Context" in found_elements or "Input Data" in found_elements):
             suggestion_text = "[TIP] Use Delimiters for Structure?"
             self.suggestions_list.insert(END, suggestion_text)
             suggestions_data[suggestion_text] = "Consider Delimiters:\n\nFor prompts with multiple distinct parts (instructions, context, examples, input), using delimiters like '###', '---', or ``` can improve clarity and help the LLM parse the sections correctly."


        # --- Suggest Techniques Based on Detected Structure/Keywords ---
        suggested_techniques = set()

        if analysis_details.get("few_shot_structure_detected"):
            tech = "Few-shot"
            if tech in PROMPT_TECHNIQUES_DATA: suggested_techniques.add(tech)

        if analysis_details.get("cot_structure_detected"):
            tech = "CoT (Chain of Thought)"
            if tech in PROMPT_TECHNIQUES_DATA: suggested_techniques.add(tech)

        if analysis_details.get("rag_structure_detected"):
            tech = "RAG (Retrieval-Augmented Generation)"
            if tech in PROMPT_TECHNIQUES_DATA: suggested_techniques.add(tech)

        # Suggest based on keywords if structure not detected
        prompt_lower = prompt.lower()
        if not suggested_techniques:
             if "example" in prompt_lower and "input" in prompt_lower and "output" in prompt_lower:
                 if "Few-shot" in PROMPT_TECHNIQUES_DATA: suggested_techniques.add("Few-shot")
             if "step-by-step" in prompt_lower or re.search(r'\b(calculate|math|logic|reason|solve)\b', prompt_lower):
                 if "CoT (Chain of Thought)" in PROMPT_TECHNIQUES_DATA: suggested_techniques.add("CoT (Chain of Thought)")
             if "context" in prompt_lower and "question" in prompt_lower or "document" in prompt_lower or "based on" in prompt_lower:
                 if "RAG (Retrieval-Augmented Generation)" in PROMPT_TECHNIQUES_DATA: suggested_techniques.add("RAG (Retrieval-Augmented Generation)")
             if "act as" in prompt_lower or "you are a" in prompt_lower or "style of" in prompt_lower or "explain like i'm" in prompt_lower:
                 if "Directional Stimulus" in PROMPT_TECHNIQUES_DATA: suggested_techniques.add("Directional Stimulus")
             if "code" in prompt_lower or "python" in prompt_lower or "javascript" in prompt_lower or "function" in prompt_lower:
                 if "PAL (Program-Aided Language Models)" in PROMPT_TECHNIQUES_DATA: suggested_techniques.add("PAL (Program-Aided Language Models)")
             if "thought:" in prompt_lower and "action:" in prompt_lower and "observation:" in prompt_lower:
                 if "ReAct (Reason and Act)" in PROMPT_TECHNIQUES_DATA: suggested_techniques.add("ReAct (Reason and Act)")


        # Add suggested techniques to the listbox
        for tech in sorted(list(suggested_techniques)): # Sort for consistency
             data = PROMPT_TECHNIQUES_DATA[tech]
             suggestion_text = f"[TECHNIQUE] Consider {tech}"
             self.suggestions_list.insert(END, suggestion_text)
             # Include technique name in Use Case description for tooltip
             tooltip_detail = f"TECHNIQUE: {data['name']}\n\n{data['description']}\n\nUse Case ({data['name']}): {data['use_case']}"
             suggestions_data[suggestion_text] = tooltip_detail

        # --- Add General Tips ---
        # Add only a few relevant general tips at the end if space allows
        general_tip_keys = list(GENERAL_TIPS.keys())
        tips_to_add_count = max(0, 5 - len(suggestions_data)) # Add up to 5 suggestions total initially
        added_tips = 0
        for key in general_tip_keys:
             if added_tips >= tips_to_add_count: break
             # Avoid adding redundant tips if specific feedback already covers it
             if key == "Be Specific" and "[!]" in [s[:3] for s in suggestions_data.keys()]: continue
             if key == "Use Action Verbs" and "[!]" in [s[:3] for s in suggestions_data.keys()]: continue
             if key == "Structure Input/Output" and "[TIP] Use Delimiters" in [s[:20] for s in suggestions_data.keys()]: continue
             if key == "Avoid Negations" and "[TIP] Rephrase Negations" in [s[:24] for s in suggestions_data.keys()]: continue

             tip_text = GENERAL_TIPS[key]
             suggestion_text = f"[GENERAL TIP] {key}"
             self.suggestions_list.insert(END, suggestion_text)
             tooltip_detail = f"GENERAL TIP: {key}\n\n{tip_text}"
             suggestions_data[suggestion_text] = tooltip_detail
             added_tips += 1


        # Store the data mapping for tooltips
        self.suggestions_data = suggestions_data

    def update_suggestion_tooltip(self, event):
        """Update tooltip for the suggestion list based on the item under cursor."""
        try:
            # Get index of item under cursor
            index = self.suggestions_list.index(f"@{event.x},{event.y}")
            suggestion_text = self.suggestions_list.get(index)
            # Retrieve full text from stored data
            full_text = self.suggestions_data.get(suggestion_text, "No details available.")
            # Update the tooltip text and schedule it
            self.suggestion_tooltip.text = full_text
            self.suggestion_tooltip.schedule_tooltip(event) # Use schedule method from Tooltip class
        except tk.TclError:
             # Error occurs if cursor is not over an item, hide tooltip
             self.suggestion_tooltip.leave()

    def show_suggestion_detail(self, event):
        """Shows the full text of a selected suggestion in a message box."""
        try:
            selected_indices = self.suggestions_list.curselection()
            if not selected_indices: return
            selected_index = selected_indices[0]
            suggestion_text = self.suggestions_list.get(selected_index)
            full_text = self.suggestions_data.get(suggestion_text, "No details available.")
            messagebox.showinfo("Suggestion Detail", full_text)
        except IndexError:
            pass

    def copy_to_clipboard(self):
        """Copies the content of the INPUT text area to the clipboard."""
        prompt_to_copy = self.input_text.get("1.0", tk.END).strip()
        if prompt_to_copy:
            try:
                pyperclip.copy(prompt_to_copy)
                messagebox.showinfo("Copied!", "Input prompt copied to clipboard.")
            except Exception as e:
                # Handle specific pyperclip errors if possible
                if "clipboard" in str(e).lower():
                     messagebox.showerror("Clipboard Error", f"Could not access the system clipboard.\nEnsure clipboard utilities are available (e.g., xclip/xsel on Linux).\n\nError: {e}")
                else:
                     messagebox.showerror("Clipboard Error", f"Could not copy to clipboard:\n{e}\n\nMake sure 'pyperclip' is installed (`pip install pyperclip`).")
        else:
            messagebox.showwarning("Empty Prompt", "Nothing to copy from the input area.")


# --- Main Execution ---
if __name__ == "__main__":
    main_window = tk.Tk()
    # Basic theming attempt (may vary by OS)
    style = ttk.Style()
    try:
        # Use a theme that generally looks better if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        # Configure Combobox style if needed
        # style.configure('TCombobox', ...)
    except tk.TclError:
        print("ttk themes not available or failed to apply.")

    main_window.configure(bg="#f0f0f0") # Set a light grey background

    app = PromptBuilderApp(main_window)
    main_window.mainloop()

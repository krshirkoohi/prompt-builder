# Enhanced Prompt Builder & Analyzer (v3)

A feature-rich Tkinter desktop app to help you write, structure, and refine AI prompts for large language models like ChatGPT, Claude, Gemini, and more. It intelligently analyses prompt components, highlights structural elements, and suggests improvements or advanced prompting techniques.

## Features
*	Smart Prompt Highlighting - Automatically detects and highlights key elements like instructions, roles, context, input/output format, delimiters, CoT triggers, and more.
*	Technique Templates - Instantly load templates for advanced prompting methods like Few-shot, CoT, RAG, ReAct, PAL, Prompt Chaining, etc.
*	Live Suggestions - Real-time suggestions and analysis based on your prompt’s content, including:
*	Structural improvements
*	Style tips
*	Recommended prompt techniques
*	Tooltips & Explanations - Hover tooltips for:
  *	Technique descriptions
  *	Suggestions
  *	Template use-cases
  *	Copy Prompt to Clipboard
* Quickly copy your final prompt for use in apps like ChatGPT or Claude.

## Requirements
*	Python 3.8+
*	Tkinter (comes with standard Python)
*	pyperclip (for clipboard functionality)

```pip install pyperclip```

## Prompt Techniques Included
* Zero-shot
* Few-shot
* Chain-of-Thought (CoT)
* ReAct (Reason and Act)
* RAG (Retrieval-Augmented Generation)
* PAL (Program-Aided Language Models)
* Prompt Chaining
* Tree of Thoughts
* Directional Stimulus
* Meta Prompting
* Graph Prompting
* Self-consistency
* Generate Knowledge

Each template comes with:
	•	A usage description
	•	When to use it
	•	A prompt template example

## Prompt Elements Analysed

The app highlights:
	•	Instruction: Verbs like “Summarise”, “Translate”, “Explain”
	•	Context: Scenario or background information
	•	Input Data: User data, examples, or questions
	•	Output Format: Expected format (JSON, table, bullet points, etc.)
	•	Role: Phrases like “Act as a…” or “You are a…”
	•	Delimiters: Markdown/code blocks like ###, ---, etc.
	•	Examples: Markers like “Example 1:”
	•	Chain-of-Thought Triggers: “Let’s think step-by-step”

## Usage
1. Run the App by scoping to the folder and using
```python main.py```

2. Start Typing
Enter or paste your prompt in the input area.

3. Use Templates
Select a technique from the dropdown to load a pre-built structure.

4. Review Analysis
Prompt elements are automatically highlighted in the Analysis area.

5. Check Suggestions
See tips and techniques that could improve your prompt.

6. Copy Prompt
Click “Copy Input Prompt” to copy your edited prompt to clipboard.

## Development Notes
*	Written using Python’s tkinter and ttk libraries
*	Modular structure allows for easy updates (new techniques, elements, etc.)
*	Tooltip handling prevents redundant pop-ups
*	Analysis is throttled to avoid running on every keystroke (debounced)

## Folder Structure

```
prompt-builder/
├── main.py
├── README.md
└── requirements.txt
```

(Add requirements.txt with pyperclip)

## License

This project is free to use, extend, or build upon. No attribution necessary. Credit welcome but not required.

## Future Improvements (Ideas)
* Save/load prompt drafts
* Export to .md or .txt
* Add dark mode
* Add support for model-specific formatting rules (ChatGPT, Claude, etc.)
* Plugin system for custom techniques

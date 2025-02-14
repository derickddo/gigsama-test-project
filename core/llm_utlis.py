from google import genai  # Ensure you have installed the appropriate library for the LLM API
import re
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


def clean_list(text_list):
    """Cleans AI-generated list items by removing bullets, asterisks, and empty strings."""
    cleaned_items = []
    for item in text_list:
        cleaned_item = re.sub(r"^\s*[-•*]+\s*", "", item).strip()  # Remove bullets and spaces
        if cleaned_item:  # Skip empty lines
            cleaned_items.append(cleaned_item)
    return cleaned_items

def process_due_date(due_date_list):
    """
    Converts relative date placeholders like "[Date 7 days from today]"
    into actual dates.
    """
    today = datetime.today()

    cleaned_due_dates = []
    for item in due_date_list:
        match = re.search(r"\[(?:Date )?(\d+) days from today\]", item)
        if match:
            days = int(match.group(1))
            actual_date = today + timedelta(days=days)
            formatted_date = actual_date.strftime("%d %b %Y")  # Example: "21 Feb 2025"
            cleaned_due_dates.append(formatted_date)
        else:
            cleaned_due_dates.append(item)  # Keep as is if no placeholder detected

    return cleaned_due_dates


def extract_actionable_steps(note_text):
    """
    Extracts actionable steps (checklist and plan) from a doctor's note using an LLM API.

    Args:
        note_text (str): The doctor's note as plain text.

    Returns:
        dict: A dictionary containing the extracted checklist and plan.
    """
    # Define the API key (ensure this is securely stored in environment variables in production)
    API_KEY = os.getenv("GEMINI_API_KEY")

    # Construct the prompt for the LLM
    content = f"""
    Extract actionable steps from the following doctor's note:

    Checklist: Immediate one-time tasks (e.g., buy a drug).
    Plan: A schedule of actions (e.g., daily reminders to take the drug for 7 days).
    Due Date: Deadlines for each plan item. eg. if plan is to take a drug for 7 days, 
    Due Date
        1. [Date 7 days from today]
    don't add Here's the breakdown of actionable steps from the doctor's note, formatted as requested, just this format:
    Checklist:
        1. ...
        2. ...
    Plan:
        1. ...
        2. ...
    Due Date:
        1. ...
        2. ...

    Doctor's Note:
    {note_text}
    """

    try:
        # Initialize the LLM client
        client = genai.Client(api_key=API_KEY)

        # Generate content using the LLM
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"text": content}]
        )

        # Splitting logic
        sections = {
            "Checklist:": "",
            "Plan:": "",
            "Due Date:": ""
        }
        generated_text = response.candidates[0].content.parts[0].text.strip()
        print(f"Generated Text: {generated_text}")  

        # Identify and extract sections
        current_section = None
        for line in generated_text.split("\n"):
            line = line.strip()

            if line in sections:  # If it's a section header
                current_section = line
            elif current_section:  # If it's content under a section
                sections[current_section] += line

        # Clean extracted text
        checklist = sections["Checklist:"].strip()
        plan = sections["Plan:"].strip()
        due_date = sections["Due Date:"].strip()
        
        
        checklist = checklist.replace("Checklist:", "").strip()
        plan = plan.strip()
        
        # Convert to list format
        checklist_list = checklist.split("\n") if checklist else []
        plan_list = plan.split("\n") if plan else []
        due_date_list = due_date.split("\n") if due_date else []
        
        # **Fix Due Date placeholders**
        due_date_list = process_due_date(due_date_list)
      
        
        return {
            "checklist": checklist_list,
            "plan": plan_list,
            "due_date": due_date_list
        }

    except Exception as e:
        print(f"Error extracting steps: {e}")
        return {"checklist": [], "plan": []}  # Return empty lists if an error occurs



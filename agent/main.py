import json
import os
import sys
from dotenv import load_dotenv
import openai
import csv
import streamlit as st
from typing import Any, List, Dict
import io
import contextlib
from datetime import datetime
from functools import lru_cache
import time
import asyncio
from concurrent.futures import TimeoutError

import config
import readinput
from knowledge_base import KnowledgeBase

TASK = """
The task is the following:
{}
"""

def fetch_validated_config(config_path: str) -> dict:
    """
    Load and validate the configuration from a specified file path.
    The function will print an error message and terminate the program if any issues
    are encountered.

    Parameters:
        config_path (str): The path to the configuration file.

    Returns:
        dict: The validated configuration dictionary.
    """
    try:
        print("Reading configuration file...")
        config_file = config.read_json(config_path)
        config.validate(config_file)
    except FileNotFoundError:
        print(f"Error: File '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as err:
        print(f"Error: Invalid JSON format in '{config_path}': {err}")
        sys.exit(1)
    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"An error occurred while reading '{config_path}': {err}")
        sys.exit(1)
    print("Successfully read configuration file")
    return config_file


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Load the dataset from the specified file path.

    Parameters:
        dataset_path (str): The path to the dataset file.

    Returns:
        list[dict[str, Any]]: The loaded dataset.
    """
    try:
        print("Reading dataset file...")
        abs_dataset_path = os.path.normpath(dataset_path)
        dataset = []
        with open(abs_dataset_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                dataset.append(row)
        print("Successfully read dataset file")
    except FileNotFoundError:
        print(f"Error: File '{dataset_path}' not found.")
        sys.exit(1)
    except Exception as err:
        print(f"An error occurred while reading '{dataset_path}': {err}")
        sys.exit(1)
    return dataset


def fetch_task(task_text: str, mvp_path: str) -> str:
    """
    Load a task from a given text input or, if not provided, request it from the user.
    The function will print an error message and terminate the program if any issues
    are encountered.

    Parameters:
        task_text (str): The text input containing the task.
        If empty or None, the task will be requested from the user.

    Returns:
        str: The loaded or inputted task.
    """
    if task_text:
        task = task_text
    else:
        print("Enter the task. When you're done, input 'END' or EOF (End Of File) to finish: ")
        mvp = config.read_file(mvp_path)
        task = readinput.read_lines()
        task += "\n\nMVP:\n" + mvp
        print("Successfully read task")
    print()
    return task

def initialize_session_state():
    """Initialize all session state variables"""
    if 'patient_data' not in st.session_state:
        st.session_state['patient_data'] = None
    if 'form_submitted' not in st.session_state:
        st.session_state['form_submitted'] = False
    if 'patient_profile' not in st.session_state:
        st.session_state['patient_profile'] = None
    if 'profile_completed' not in st.session_state:
        st.session_state['profile_completed'] = False
    if 'current_agent_index' not in st.session_state:
        st.session_state['current_agent_index'] = 0
    if 'questions_asked' not in st.session_state:
        st.session_state['questions_asked'] = 0
    if 'patient_details' not in st.session_state:
        st.session_state['patient_details'] = None
    if 'waiting_for_patient_details' not in st.session_state:
        st.session_state['waiting_for_patient_details'] = True
    if 'input_key' not in st.session_state:
        st.session_state['input_key'] = 0
    if 'iteration' not in st.session_state:
        st.session_state['iteration'] = 1
    if 'collecting_user_input' not in st.session_state:
        st.session_state['collecting_user_input'] = True
    if 'is_processing' not in st.session_state:
        st.session_state['is_processing'] = False
    if 'last_input' not in st.session_state:
        st.session_state['last_input'] = None
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
    if 'asked_questions' not in st.session_state:
        st.session_state['asked_questions'] = []
    if 'patient_answers' not in st.session_state:
        st.session_state['patient_answers'] = {}
    if 'conversation_stage' not in st.session_state:
        st.session_state['conversation_stage'] = 'diagnostic'
    if 'diagnosis_complete' not in st.session_state:
        st.session_state['diagnosis_complete'] = False
    if 'force_diagnosis' not in st.session_state:
        st.session_state['force_diagnosis'] = False

def reset_session():
    """Reset the session state for a new conversation"""
    st.session_state['current_agent_index'] = 0
    st.session_state['questions_asked'] = 0
    st.session_state['patient_data'] = None
    st.session_state['form_submitted'] = False
    st.session_state['patient_details'] = None
    st.session_state['waiting_for_patient_details'] = True
    st.session_state['iteration'] = 1
    st.session_state['collecting_user_input'] = True
    st.session_state['input_key'] += 1
    st.session_state['chat_messages'] = []
    st.session_state['asked_questions'] = []
    st.session_state['patient_answers'] = {}
    st.session_state['conversation_stage'] = 'diagnostic'
    st.session_state['diagnosis_complete'] = False

# Add new function to handle dataset-based questioning
def get_relevant_questions(symptom: str, dataset: List[Dict[str, Any]]) -> List[str]:
    """Get relevant follow-up questions based on the symptom from dataset."""
    for entry in dataset:
        if entry['symptom'].lower() in symptom.lower():
            return [q.strip() for q in entry['follow_up_questions'].split(';')]
    return []

def get_possible_conditions(symptom: str, dataset: List[Dict[str, Any]]) -> List[str]:
    """Get possible conditions based on the symptom from dataset."""
    for entry in dataset:
        if entry['symptom'].lower() in symptom.lower():
            return [c.strip() for c in entry['conditions'].split(',')]
    return []

def collect_patient_profile():
    """Collect initial patient profile details"""
    st.write("### Patient Profile")
    
    # Create form with unique key
    with st.form(key="patient_profile_form"):
        age = st.number_input("Age", min_value=0, max_value=120)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        known_conditions = st.text_area("Known Medical Conditions (separate with commas)")
        current_medications = st.text_area("Current Medications (separate with commas)")
        submit_button = st.form_submit_button("Submit Profile")

        if submit_button:
            # Store form data in session state
            st.session_state['patient_data'] = {
                "age": age,
                "gender": gender,
                "known_conditions": [c.strip() for c in known_conditions.split(',') if c.strip()],
                "medications": [m.strip() for m in current_medications.split(',') if m.strip()]
            }
            st.session_state['form_submitted'] = True
            return True
    return False

def get_agent_prompt(agent_name: str, dataset: List[Dict[str, Any]]) -> str:
    """Generate appropriate prompt based on agent type and conversation stage"""
    profile = st.session_state.get('patient_data', {})
    conversation_context = "\n".join([
        f"{'Patient' if msg[0] == 'user' else msg[0].capitalize()}: {msg[1]}"
        for msg in st.session_state.chat_messages
    ])
    
    if agent_name == "DiagnosticAgent":
        if st.session_state.get('force_diagnosis', False):
            return (
                f"You are conducting a medical diagnosis. Review this conversation:\n\n{conversation_context}\n\n"
                "The patient has requested a diagnosis. Based on the information gathered:\n"
                "1. Provide a clear and concise diagnostic assessment\n"
                "2. End with '[DIAGNOSIS_COMPLETE]'\n"
                "Be professional and focused on the most likely conditions based on the symptoms discussed."
            )
        else:
            return (
                f"You are conducting a medical diagnosis. Review this conversation:\n\n{conversation_context}\n\n"
                "Based on the symptoms and responses, ask a relevant follow-up question to gather more information.\n"
                "Be concise and focused. Never repeat questions already asked."
            )
    
    elif agent_name == "RecommendationAgent":
        return (
            f"Based on this diagnostic conversation:\n\n{conversation_context}\n\n"
            "Provide specific, practical treatment recommendations. "
            "Include both immediate relief suggestions and long-term management strategies. "
            "End with '[RECOMMENDATIONS_COMPLETE]'"
        )
    
    else:  # ExplanationAgent
        return (
            f"Based on this conversation:\n\n{conversation_context}\n\n"
            "Explain the reasoning behind the diagnosis and recommendations. "
            "Include what led to this conclusion and why the recommendations are appropriate. "
            "End with '[EXPLANATION_COMPLETE]'"
        )

def display_message(sender: str, content: str):
    """Display a message with appropriate styling in Streamlit"""
    content = content.replace("###", "").replace(sender, "").strip()
    
    if "User:" in sender:
        st.session_state.chat_messages.append(("user", content))
    elif "DiagnosticAgent" in sender:
        st.session_state.chat_messages.append(("diagnostic", content))
    elif "RecommendationAgent" in sender:
        st.session_state.chat_messages.append(("recommendation", content))
    elif "ExplanationAgent" in sender:
        st.session_state.chat_messages.append(("explanation", content))

@lru_cache(maxsize=100)
def get_cached_agent_prompt(agent_name: str, conversation_key: str) -> str:
    # ...existing get_agent_prompt code...
    pass

def process_agent_response(response: str, agent_name: str) -> None:
    """Process agent response and manage conversation flow."""
    if agent_name == "DiagnosticAgent":
        if "[DIAGNOSIS_COMPLETE]" in response:
            response = response.replace("[DIAGNOSIS_COMPLETE]", "").strip()
            st.session_state['conversation_stage'] = 'recommendation'
            st.session_state['diagnosis_complete'] = True
    
    elif agent_name == "RecommendationAgent":
        if "[RECOMMENDATIONS_COMPLETE]" in response:
            response = response.replace("[RECOMMENDATIONS_COMPLETE]", "").strip()
            st.session_state['conversation_stage'] = 'explanation'
    
    elif agent_name == "ExplanationAgent":
        if "[EXPLANATION_COMPLETE]" in response:
            response = response.replace("[EXPLANATION_COMPLETE]", "").strip()
            st.session_state['conversation_stage'] = 'complete'
    
    display_message(f"{agent_name}:", response)

def process_user_input(user_input: str, dataset: List[Dict[str, Any]], agents: Dict[str, Any]) -> None:
    """Process user input with improved error handling and timeouts."""
    if not user_input or user_input == st.session_state.get('last_input'):
        return

    st.session_state['is_processing'] = True
    st.session_state['last_input'] = user_input
    
    try:
        with st.spinner('Processing...'):
            display_message("User:", user_input)
            
            if st.session_state['conversation_stage'] == 'diagnostic':
                agent = agents["DiagnosticAgent"]
                prompt = get_agent_prompt("DiagnosticAgent", dataset)
                
                # Add strict timeout for API calls
                start_time = time.time()
                try:
                    with st.spinner('Getting diagnostic response...'):
                        response = agent.get_full_response(prompt)
                        if time.time() - start_time > 30:  # 30 seconds timeout
                            raise TimeoutError("Response took too long")
                except Exception as e:
                    st.error("API call failed. Please try again.")
                    return
                
                process_agent_response(response, "DiagnosticAgent")
                
                # If diagnosis is complete, proceed with other agents
                if st.session_state['diagnosis_complete']:
                    for next_agent in ["RecommendationAgent", "ExplanationAgent"]:
                        try:
                            with st.spinner(f'Getting {next_agent} response...'):
                                agent = agents[next_agent]
                                prompt = get_agent_prompt(next_agent, dataset)
                                response = agent.get_full_response(prompt)
                                process_agent_response(response, next_agent)
                        except Exception as e:
                            st.error(f"{next_agent} API call failed. Please try again.")
                            return
                    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        st.session_state['is_processing'] = False
        st.session_state['force_diagnosis'] = False

def render_conversation_ui(dataset: List[Dict[str, Any]], agents: Dict[str, Any]):
    """Render the conversation UI with improved layout."""
    st.write("### Diagnostic Session")
    
    # Display conversation history with enhanced formatting
    for msg_type, content in st.session_state.chat_messages:
        if msg_type == "user":
            st.info(f"👤 Patient: {content}")
        elif msg_type == "diagnostic":
            with st.success("🔍 Diagnostic Assessment"):
                st.write(content)
                if "[DIAGNOSIS_COMPLETE]" in content:
                    st.write("---")
                    st.write("*Diagnosis phase complete*")
        elif msg_type == "recommendation":
            with st.warning("💊 Treatment Recommendations"):
                recommendations = [r.strip() for r in content.split('.') if r.strip()]
                for rec in recommendations:
                    if rec and not rec.endswith('[RECOMMENDATIONS_COMPLETE]'):
                        st.write(f"• {rec}")
                if "[RECOMMENDATIONS_COMPLETE]" in content:
                    st.write("---")
                    st.write("*Recommendations phase complete*")
        elif msg_type == "explanation":
            with st.info("📝 Medical Explanation"):
                st.markdown(content.replace("[EXPLANATION_COMPLETE]", "\n\n*Explanation phase complete*"))

    # Show input field and buttons during diagnostic stage
    if st.session_state['conversation_stage'] == 'diagnostic':
        st.write("---")
        if st.session_state['questions_asked'] == 0:
            st.write("Please describe your main symptoms:")
        
        # Use columns for better button layout
        user_input = st.text_input(
            "Your message:",
            key=f"user_input_{st.session_state['input_key']}",
            disabled=st.session_state['is_processing']
        )
        
        # Create a row of buttons
        col1, col2 = st.columns(2)
        
        with col1:
            send_button = st.button(
                "Send",
                key="send_button",
                disabled=st.session_state['is_processing'],
                use_container_width=True
            )
        
        with col2:
            complete_button = st.button(
                "Complete Diagnosis",
                key="complete_button",
                type="primary",
                disabled=st.session_state['is_processing'] or not st.session_state.chat_messages,
                use_container_width=True
            )

        if send_button and user_input:
            process_user_input(user_input, dataset, agents)
            st.rerun()
        
        if complete_button:
            st.session_state['force_diagnosis'] = True
            process_user_input("Please provide the diagnosis now.", dataset, agents)
            st.rerun()

    # Show completion message and reset button
    elif st.session_state['conversation_stage'] == 'complete':
        st.success("### Diagnostic Session Complete!")
        if st.button("Start New Conversation", type="primary", use_container_width=True):
            reset_session()
            st.rerun()

def main() -> None:
    # Load environment variables and setup
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-..."):
        st.error("Error: Please set a valid OPENAI_API_KEY in your .env file")
        st.stop()
    
    openai.api_key = api_key

    # Load configuration and dataset
    config_file = fetch_validated_config("agent.json")
    agent_order = config_file["agent_order"]
    agents = config.create_coloragents(config_file)
    dataset = load_dataset(config_file["dataset"])

    # Initialize knowledge base (simplified)
    kb = KnowledgeBase()
    kb.load_dataset(dataset)
    
    # Replace the old dataset-based functions with knowledge base calls
    def get_relevant_questions(symptom: str, dataset: List[Dict[str, Any]]) -> List[str]:
        return kb.get_relevant_questions(symptom)

    def get_possible_conditions(symptom: str, dataset: List[Dict[str, Any]]) -> List[str]:
        return kb.get_possible_conditions(symptom)

    # Create a string buffer to capture terminal output
    terminal_output = io.StringIO()

    # Initialize session state
    initialize_session_state()
    
    if 'terminal_history' not in st.session_state:
        st.session_state['terminal_history'] = ""

    st.title("Medical Diagnostic Assistant")
    
    # Display patient profile if available
    if st.session_state.get('patient_data'):
        with st.sidebar.expander("Patient Profile", expanded=True):
            profile = st.session_state['patient_data']
            st.markdown(f"""
            ### Patient Information
            - **Age:** {profile['age']}
            - **Gender:** {profile['gender']}
            - **Known Conditions:** {', '.join(profile['known_conditions']) if profile['known_conditions'] else 'None'}
            - **Current Medications:** {', '.join(profile['medications']) if profile['medications'] else 'None'}
            """)
    
    # Handle patient profile collection first
    if not st.session_state.get('form_submitted', False):
        if collect_patient_profile():
            st.rerun()
        st.stop()
    
    # Render the main conversation interface
    render_conversation_ui(dataset, agents)
    
    # # Add reset button at the bottom
    # st.write("---")
    # if st.button("Start New Consultation"):
    #     reset_session()
    #     st.session_state['terminal_history'] = ""
    #     st.rerun()

if __name__ == "__main__":
    main()
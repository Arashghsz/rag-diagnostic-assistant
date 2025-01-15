"""
This module provides functions for reading
a JSON configuration file, creating ColorAgent instances,
and parsing command line arguments for the program.
"""
import argparse
import json
import os
from typing import Any

from agent import ColorAgent


REQ_CONFIQ_FIELDS = ["agent_order", "agents", "max_tokens_per_call", "openai_model"]
REQ_AGENT_FIELD = ["name", "temperature", "color", "max_history", "system", "user"]


def read_file(file_path: str) -> str:
    """
    Read the file and return the content.

    Parameters:
        file_path (str): The path to the file.

    Returns:
        str: The file content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    # Convert relative path to absolute path
    abs_path = os.path.abspath(file_path)
    with open(abs_path, "r", encoding="utf-8") as file:
        return file.read()


def read_json(file_path: str) -> dict[str, Any]:
    """
    Read the JSON file and return it as an object of dictionaries and lists.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        dict: A JSON object converted to dictionaries and lists.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If an error occurs during JSON parsing.
    """
    json_content = read_file(file_path)
    config_data = json.loads(json_content)
    return config_data


def validate(config_file: dict[str, Any]) -> None:
    """
    Validates the config JSON file.

    The config file should contain the following fields:
        - "agent_order" (list[str]): The agent pipeline.
        - "agents" (list[dict]): The agents.
        - "max_tokens_per_call" (int): Tokens per call.
        - "openai_model" (str): The OpenAI model to use.
    Optional field:
        - "iterations" (int): The number of repetitions.

    Each agent should have the following keys:
        - "name" (str): Name of the agent
        - "color" (str): Color for the agent
        - "max_history" (int): Maximum message history for the agent
        - "temperature" (float): Temperature value for message generation
        - "system" (str): System description for the agent
        - "user" (str): User message for the agent
    Optional fields
        - "top_p" (float): Top-p value for message generation (default: 1.0)

    Args:
        config_file (dict[str, Any]): JSON file with the

    Raises:
        ValueError: If JSON file is missing a field.
    """
    # Validation for required fields in JSON file
    for field in REQ_CONFIQ_FIELDS:
        if field not in config_file:
            raise ValueError(
                f"'{field}' is missing in the main JSON configuration file"
            )
    # Validation for agents in JSON file
    for agent_config in config_file["agents"]:
        for field in REQ_AGENT_FIELD:
            if field not in agent_config:
                raise ValueError(
                    f"'{field}' is missing in the agent JSON configuration file"
                )


def create_coloragents(config: dict) -> dict[str, ColorAgent]:
    """
    Create ColorAgent instances based on the provided configuration.

    Parameters:
        agents_config (list[dict]): List of dictionaries
        representing agent configurations.

    Returns:
        dict[str, ColorAgent]: A dictionary mapping agent names to ColorAgent instances.

    Returns a dictionary containing ColorAgent instances, where keys are agent names.
    """

    agents: dict[str, ColorAgent] = {}
    for agent_config in config["agents"]:
        agent = ColorAgent(
            name=agent_config["name"],
            color=agent_config["color"],
            openai_model=config["openai_model"],
            max_tokens_per_call=config["max_tokens_per_call"],
            max_history=agent_config["max_history"],
            top_p=agent_config.get("top_p", 1.0),
            temperature=agent_config["temperature"],
        )
        if "system" in agent_config:
            agent.append_message("system", agent_config["system"], False)
        if "user" in agent_config:
            agent.append_message("user", agent_config["user"], False)
        agents[agent_config["name"]] = agent
    return agents


def parse_argument() -> argparse.Namespace:
    """
    Parse command line arguments for the program.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Autonomous-AI-Agent-Team-Coding-System. "
        "To get started, look at the README.md file."
    )
    parser.add_argument(
        "config_file",
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Path to the task description file.",
        default="",
    )
    parser.add_argument("-m", "--mvp", help="The path to the MVP file.")  # New code

    # Use Streamlit to get the arguments
    args = parser.parse_args()
    args.config_file = st.text_input("Config File Path", value=args.config_file)
    args.input = st.text_input("Input File Path", value=args.input)
    args.mvp = st.text_input("MVP File Path", value=args.mvp)
    
    return args

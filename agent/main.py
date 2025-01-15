import json
import sys
import os
from dotenv import load_dotenv

import colorama
import openai
from typing import Any
import csv

import config
import readinput


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


def load_dataset(dataset_path: str) -> list[dict[str, Any]]:
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


def fetch_task(input_path: str,mvp_path: str) -> str:
    """
    Load a task from a given file path or, if not provided, request it from the user.
    The function will print an error message and terminate the program if any issues
    are encountered.

    Parameters:
        input_path (str): The path to the input file containing the task.
        If empty or None, the task will be requested from the user.

    Returns:
        str: The loaded or inputted task.
    """
    if input_path:
        try:
            print("Reading input file...")
            task = config.read_file(input_path)
            print("Successfully read input file")
        except FileNotFoundError:
            print(f"Error: File '{input_path}' not found.")
            sys.exit(1)
        except Exception as err:
            print(f"An error occurred while reading '{input_path}': {err}")
            sys.exit(1)
    else:
        print(
            "Enter the task. "
            f'When you\'re done, input "{colorama.Fore.BLUE}END{colorama.Fore.RESET}" '
            "or EOF (End Of File) to finish: "
        )
        mvp = config.read_file(mvp_path)
        task = readinput.read_lines()
        task += "\n\nMVP:\n" + mvp
        print("Successfully read task")
    print()
    return task

def main() -> None:
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-..."):
        print("Error: Please set a valid OPENAI_API_KEY in your .env file")
        print("You can get your API key from https://platform.openai.com/account/api-keys")
        sys.exit(1)
    
    openai.api_key = api_key

    args = config.parse_argument()
    
    if not args.mvp:
        print("Error: MVP file path is required")
        sys.exit(1)

    # Load configuration file and create agents
    config_file = fetch_validated_config(args.config_file)
    agents = config.create_coloragents(config_file)
    agent_order = config_file["agent_order"]
    iterations = config_file.get("iterations", 1)

    # Load the dataset
    dataset = load_dataset(config_file["dataset"])

    # Fetch the initial task
    task = fetch_task(args.input, args.mvp)
    conversation_history = f"Initial Context:\n{task}\n\n"

    for iteration in range(iterations):
        print(f"\n=== Iteration {iteration + 1} ===")
        
        for agent_name in agent_order:
            agent_config = next(
                (agent for agent in config_file["agents"] if agent["name"] == agent_name),
                None
            )
            if not agent_config:
                continue

            task_info = agent_config["tasks"].get(str(iteration + 1))
            if task_info:
                task = f"{task_info}\n\nContext:\n{conversation_history}\n\nDataset:\n{dataset}"
                print(f"\n-> {agent_name}'s task: {task_info}")
                
                agent = agents[agent_name]
                response = agent.get_full_response(task)
                conversation_history += f"{agent_name}:\n{response}\n\n"

    print("\n=== Final Analysis ===")
    print(conversation_history)

if __name__ == "__main__":
    main()
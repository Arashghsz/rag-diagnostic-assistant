"""
This module contains classes and functions to interact with the OpenAI API.
"""

from collections import deque
import os
import typing
import openai
import time

from printer import COLORS, ColorPrinter

openai.api_key = os.getenv("OPENAI_API_KEY")

def make_message(
    role: typing.Literal["system", "user", "assistant"], content: str
) -> dict[str, str]:
    """
    Constructs a dictionary representing a message.
    """
    if role not in ("system", "user", "assistant"):
        raise ValueError(f"Invalid role: {role}")
    return {"role": role, "content": content}

class Agent:
    """
    Represents an agent that interacts with the OpenAI API.
    """

    def __init__(
        self,
        openai_model: str,
        max_tokens_per_call: int,
        max_history: int,
        timeout: int = 30,  # Add timeout parameter
        **kwargs,
    ) -> None:
        """
        Initialize the Agent object.
        """
        self._openai_model = openai_model
        self._max_tokens = max_tokens_per_call
        self._history: deque[dict[str, str]] = deque()
        self._max_history = max_history
        self._timeout = timeout
        self._openai_kwargs = kwargs
        self._messages: list[dict[str, str]] = []

    def append_message(
        self,
        role: typing.Literal["system", "user", "assistant"],
        content: str,
        history: bool = True,
    ) -> None:
        """
        Add a new message to either the agent's history or permanent messages.
        """
        if history:
            self._history.append(make_message(role, content))
        else:
            self._messages.append(make_message(role, content))

    def generate_response(self, user_message: str = "") -> typing.Iterator[str]:
        """
        Sends the accumulated messages (permanent and history) to the OpenAI API and
        yields the assistant's response in an Iterator stream.
        """
        while len(self._history) > self._max_history:
            self._history.popleft()

        if user_message:
            self._history.append(make_message("user", user_message))

        completion_stream = openai.ChatCompletion.create(  # type: ignore
            model=self._openai_model,
            max_tokens=self._max_tokens,
            messages=self._messages + list(self._history),
            stream=True,
            **self._openai_kwargs,
        )
        for chunk in completion_stream:
            response = chunk.choices[0]["delta"]  # type: ignore
            if "content" not in response:
                continue
            message = response.content  # type: ignore
            if self._history and self._history[-1]["role"] == "assistant":
                self._history[-1]["content"] += message
            else:
                self._history.append(make_message("assistant", message))

            yield message

    def get_full_response(self, user_message: str = "") -> str:
        """
        Sends the accumulated messages (permanent and history) to the OpenAI API and
        returns the assistant's full response.
        """
        start_time = time.time()
        try:
            messages = self.generate_response(user_message)
            response = "".join(messages)
            if time.time() - start_time > self._timeout:
                raise TimeoutError("Response took too long")
            return response
        except Exception as e:
            print(f"Error getting response: {e}")
            raise

class ColorAgent(Agent):
    """
    An Agent subclass providing colored console output.
    """

    def __init__(
        self,
        name: str,
        color: str,
        openai_model: str,
        max_tokens_per_call: int,
        max_history: int,
        **kwargs,
    ) -> None:
        """
        Initialize the ColorAgent with a specified color.
        """
        super().__init__(
            openai_model,
            max_tokens_per_call=max_tokens_per_call,
            max_history=max_history,
            **kwargs,
        )
        self._name = name
        if color not in COLORS:
            raise ValueError(f"Agent '{name}' has an invalid color: {color}")
        self._color_printer = ColorPrinter(color)

    def generate_response(self, user_message: str = "") -> typing.Iterator[str]:
        """
        Sends messages to the OpenAI API, yields the response, and prints the response
        in the specified color.
        """
        self._color_printer(f"### {self._name} ###")
        for message in super().generate_response(user_message):
            self._color_printer(message, end="")
            yield message
        self._color_printer("\n\n")

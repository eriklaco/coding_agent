"""Agent loop: model ↔ tools until plain text or iteration cap."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import cast

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
)
from openai.types.chat.chat_completion_message_function_tool_call_param import (
    ChatCompletionMessageFunctionToolCallParam,
)
from rich.console import Console

from coding_agent.config import MAX_TOOL_ITERATIONS
from coding_agent.debug import DebugTracer
from coding_agent.history import trim_history
from coding_agent.prompts import CONTINUE_WITH_TOOL_PROMPT, SYSTEM_PROMPT
from coding_agent.tool_parse import (
    extract_tool_calls_from_text,
    looks_like_deferred_tool_use,
)
from coding_agent.tools import make_tool_bundle
from coding_agent.tools.base import ApprovalGate
from coding_agent.ui import ToolTracer, TurnClock


class Agent:
    def __init__(
        self,
        client: OpenAI,
        model: str,
        gate: ApprovalGate,
        *,
        console: Console | None = None,
        debug: bool = False,
        max_tool_iterations: int = MAX_TOOL_ITERATIONS,
    ) -> None:
        self.client = client
        self.model = model
        self.console = console or Console()
        self.tracer = ToolTracer(self.console)
        self.clock = TurnClock(self.console)
        self.debug = DebugTracer(self.console, enabled=debug)
        self.max_tool_iterations = max_tool_iterations
        self.tool_schemas: list[ChatCompletionToolParam]
        self.executors: dict[str, Callable[..., str]]
        self.tool_schemas, self.executors = make_tool_bundle(gate)
        self.messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

    @property
    def last_turn_elapsed(self) -> float:
        """Seconds for the most recently finished run_turn (0 if none yet)."""
        return self.clock.last_elapsed

    def run_turn(self, user_input: str) -> str:
        self.clock.start()
        self.messages.append({"role": "user", "content": user_input})

        try:
            return self._run_turn_loop()
        finally:
            self.clock.stop()

    def _run_turn_loop(self) -> str:
        nudged = False
        for iteration in range(self.max_tool_iterations):
            self.messages = trim_history(self.messages)
            self.debug.request(
                model=self.model,
                messages=list(self.messages),
                tools=list(self.tool_schemas),
                tool_choice="auto",
                iteration=iteration + 1,
            )
            with self.clock.waiting("thinking"):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=self.tool_schemas,
                    tool_choice="auto",
                )
            choice = response.choices[0]
            msg = choice.message
            self.debug.response(
                message=msg,
                iteration=iteration + 1,
                finish_reason=choice.finish_reason,
            )

            function_calls = self._collect_function_calls(msg)
            if not function_calls:
                content = msg.content or ""
                # Local models often narrate the next tool instead of calling it.
                if (
                    not nudged
                    and looks_like_deferred_tool_use(content)
                    and iteration + 1 < self.max_tool_iterations
                ):
                    nudged = True
                    self.messages.append({"role": "assistant", "content": content})
                    self.messages.append({"role": "user", "content": CONTINUE_WITH_TOOL_PROMPT})
                    if self.debug.enabled:
                        self.console.print(
                            "[yellow]note:[/yellow] model deferred a tool call; nudging once"
                        )
                    continue

                self.messages.append({"role": "assistant", "content": content})
                return content

            # Prefer a short prose lead-in; hide raw JSON tool dumps from history noise.
            lead_in = (msg.content or "").strip()
            if lead_in and extract_tool_calls_from_text(lead_in, known_tools=set(self.executors)):
                lead_in = ""

            assistant_msg: ChatCompletionAssistantMessageParam = {
                "role": "assistant",
                "content": lead_in or None,
                "tool_calls": function_calls,
            }
            self.messages.append(assistant_msg)

            for call in function_calls:
                result = self._execute_tool(
                    call["function"]["name"],
                    call["function"]["arguments"],
                )
                tool_msg: ChatCompletionToolMessageParam = {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": str(result),
                }
                self.messages.append(tool_msg)

        return "(stopped: hit max tool-call iterations for this turn)"

    def _collect_function_calls(
        self,
        msg: object,
    ) -> list[ChatCompletionMessageFunctionToolCallParam]:
        tool_calls = getattr(msg, "tool_calls", None)
        function_calls: list[ChatCompletionMessageFunctionToolCallParam] = []
        if tool_calls:
            for tool_call in tool_calls:
                if getattr(tool_call, "type", None) != "function":
                    continue
                function = tool_call.function
                function_calls.append(
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": function.name,
                            "arguments": function.arguments or "{}",
                        },
                    }
                )
            if function_calls:
                return function_calls

        # Local models often print a tool call as JSON text instead of tool_calls.
        content = getattr(msg, "content", None) or ""
        recovered = extract_tool_calls_from_text(
            content,
            known_tools=set(self.executors),
        )
        if recovered and self.debug.enabled:
            self.console.print(
                "[yellow]note:[/yellow] model returned a tool call as text; "
                "running it via fallback parser"
            )
        return recovered

    def _execute_tool(self, name: str, arguments_json: str) -> str:
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError:
            return f"ERROR: model sent malformed JSON arguments: {arguments_json!r}"

        if not isinstance(args, dict):
            return f"ERROR: tool arguments must be a JSON object, got {type(args).__name__}"

        executor: Callable[..., str] | None = self.executors.get(name)
        if executor is None:
            return f"ERROR: unknown tool '{name}'"

        typed_args = cast(dict[str, object], args)
        try:
            self.tracer.tool_start(name, typed_args)
            result = executor(**typed_args)
        except Exception as e:
            result = f"ERROR: {e}"
        self.tracer.tool_end(name, result)
        return result

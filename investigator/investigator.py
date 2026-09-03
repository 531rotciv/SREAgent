import json
from typing import Any
import re
from tools.tools import TOOL_DEFINITIONS
from llm_operation.system_prompt import _system_prompt
from investigator.synthesizer import Synthesizer


SYSTEM_PROMPT = _system_prompt()

# Investigator class orchestrates the investigation process by interacting with the LLM, GitHub, and Observability clients.
class Investigator:

    def __init__(
        self,
        llm,
        github,
        observability,

    ):
        self.llm = llm
        self.github = github
        self.observability = observability

        # Tool map is a dictionary that maps tool names to their corresponding functions.
        self.tool_map = {
            "get_metrics": observability.get_metrics,
            "search_logs": observability.search_logs,
            "get_recent_deployments": github.get_recent_deployments,
            "get_recent_pull_requests": github.get_recent_pull_requests,
            "get_pull_request": github.get_pull_request,
            "get_code_owners_for_path": github.get_code_owners_for_path,
        }

    def investigate_stream(self, alert_id: str):
        """Generator that yields investigation progress and final synthesis as text chunks."""

        # The alert is the input that triggered the investigation.
        alert = self.observability.get_alert(alert_id)

        if alert is None:
            raise ValueError(
                f"Alert not found: {alert_id}"
            )
        # Initialize the conversation messages with the system prompt and the alert.
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "Investigate the following production alert.\n\n"
                    f"{json.dumps(alert, indent=2)}"
                ),
            },
        ]

        evidence = []
        yield self.event(
            "starting",
            text="INVESTIGATION STARTED\n"
        ) 
        # Iteratively generates model responses, executes tool calls, and yields progress events until no more tools are requested.
        # In production environment, you may want to add a maximum iteration limit to prevent infinite loops and ballooning token costs.
        while True:
            yield self.event(
                "progress",
                text="\n" + "=" * 60 + "\n"
            )             

            yield self.event(
                "progress",
                text="AGENT: Thinking about next investigation step...\n"
            )             

            response = self.llm.generate(
                messages=messages,
                tools=TOOL_DEFINITIONS
            )
            yield self.event(
                "progress",
                text="\nMODEL RESPONSE:\n"
            ) 

            yield self.event(
                "progress",
                text=response + "\n"
            )             


            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                print("\nAGENT: No more tools requested.\n")
                break

            messages.append({
                "role": "assistant",
                "content": response,
            })

            # Tool calls are executed sequentially, and their results are yielded as events for streaming.
            for tool_call in tool_calls:
                yield self.event(
                    "tool_call",
                    text="\n" + "-" * 60 + "\n"
                )                 

                yield self.event(
                    "tool_call",
                    text=f"TOOL CALL: {tool_call['name']}\n"
                )                 

                yield self.event(
                    "tool_call",
                    text=f"ARGUMENTS: {json.dumps(tool_call['arguments'])}\n"
                )                 

                result = self._execute_tool(tool_call)

                yield self.event(
                    "tool_call",
                    text="TOOL RESULT:\n"
                ) 

                yield self.event(
                    "tool_result",
                    text=json.dumps(result, indent=2) + "\n"
                )         

                evidence.append({
                    "tool": tool_call["name"],
                    "arguments": tool_call["arguments"],
                    "result": result,
                })

                messages.append({
                    "role": "tool",
                    "name": tool_call["name"],
                    "content": json.dumps(result),
                })
 

        yield self.event(
            "investigation_complete",
            text="INVESTIGATION COMPLETE\n"
        )          

        yield self.event(
            "investigation_complete",
            text=f"Evidence items collected: {len(evidence)}\n",
        )        

        yield self.event(
            "investigation_complete",
            text="=" * 60 + "\n",
        )
        yield self.event(
            "synthesis_start",
            text="Generating final synthesis...",
        )

        # The final synthesis is generated after all evidence has been collected, 
        # and it is yielded as a single event for streaming.
        synthesis = Synthesizer(self.llm).synthesize(
            alert=alert,
            evidence=evidence,
        )

        yield self.event(
            "complete",
            text=synthesis
        )
    # Helper function to format events as JSON strings for streaming responses. 
    # Each event includes a type and associated data, allowing the frontend to handle different types of updates during the investigation process.
    def event(self,event_type: str, **data) -> str:
        return json.dumps({
            "type": event_type,
            **data,
        }) + "\n"

    # Helper function to execute a tool call based on the model's request.
    def _execute_tool(
        self,
        tool_call: dict[str, Any],
    ) -> Any:
        print("In execute tool")
        tool_name = tool_call["name"]
        arguments = tool_call["arguments"]
        print(tool_name)
        print(arguments)

        tool = self.tool_map.get(tool_name)
        print(tool)
        if tool is None:
            raise ValueError(
                f"Unknown tool requested: {tool_name}"
            )

        return tool(**arguments)
    
    # Helper function to extract tool calls from the model's response.
    @staticmethod
    def _extract_tool_calls(response: str) -> list[dict]:
        """Extract tool calls from the model response."""

        if not response:
            return []

        matches = re.findall(
            r"<tool_call>\s*(.*?)\s*</tool_call>",
            response,
            re.DOTALL,
        )

        tool_calls = []

        for match in matches:
            try:
                parsed = json.loads(match)
            except json.JSONDecodeError:
                continue

            if not isinstance(parsed, dict):
                continue

            if "name" not in parsed:
                continue

            tool_calls.append({
                "name": parsed["name"],
                "arguments": parsed.get("arguments", {}),
            })

        return tool_calls    
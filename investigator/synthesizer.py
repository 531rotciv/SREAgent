import json

SYNTHESIZER_SYSTEM_PROMPT = """
You are an SRE incident analyst.

Your task is to analyze incident evidence and produce an
accurate, evidence-backed assessment.

Never invent evidence. Clearly distinguish observed facts
from hypotheses.
"""

class Synthesizer:

    def __init__(self, llm):
        self.llm = llm

    def synthesize(
        self,
        alert: dict,
        evidence: list[dict],
    ):

        prompt = self._build_prompt(
            alert,
            evidence,
        )

        response = self.llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": SYNTHESIZER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt
                },

            ],
            max_new_tokens= 1512
        )

        return response

    # Creates the prompt for the Synthesizer LLM based on the alert and evidence collected during the investigation.
    @staticmethod
    def _build_prompt(
        alert: dict,
        evidence: list[dict],
    ) -> str:

        return f"""
        Investigate the following production incident using the
        evidence collected by the investigation agent.

        ALERT:
        {json.dumps(alert, indent=2)}

        EVIDENCE:
        {json.dumps(evidence, indent=2)}

        Analyze the provided evidence and:

        1. Summarize what happened.
        2. Identify the most likely root cause.
        3. State your confidence in the root cause.
        4. Explain the reasoning behind the hypothesis.
        5. Cite the evidence that supports the hypothesis.
        6. Provide actionable recommendations for the on-call engineer.


        Do not invent evidence or information that is not provided.
        """

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, ConfigDict

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str


class GroqService:
    def __init__(self):
        self.model = os.getenv(
            "GROQ_MODEL", "openai/gpt-oss-20b"
        )
        self.client = Groq(
            api_key=os.environ["GROQ_API_KEY"],
            timeout=30.0,
            max_retries=2,
        )

    def generate(self, question: str) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant. "
                        "Return a concise answer in JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "llm_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"}
                        },
                        "required": ["answer"],
                        "additionalProperties": False,
                    },
                },
            },
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Groq returned an empty response")

        return LLMResponse.model_validate_json(content)

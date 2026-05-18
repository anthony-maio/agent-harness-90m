"""Summarize text using the configured LLM."""

import os

from litellm import completion

NAME = "summarize"
DESCRIPTION = "Summarize a block of text into a concise paragraph."
PARAMETERS = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "The text to summarize",
        },
        "max_sentences": {
            "type": "integer",
            "description": "Maximum number of sentences in the summary (default: 3)",
            "default": 3,
        },
    },
    "required": ["text"],
}


def execute(text: str, max_sentences: int = 3) -> str:
    try:
        response = completion(
            model=os.environ.get("SUMMARIZE_MODEL", "openai/gpt-4o-mini"),
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following text in {max_sentences} sentences or fewer. Be direct and specific.\n\n{text[:6000]}",
                }
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content or "No summary generated."
    except Exception as e:
        return f"Summarization failed: {e}"

import os
import json
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
_has_key = bool(api_key)
_client = OpenAI(api_key=api_key, timeout=15) if _has_key else None


class LLM:

    def call(self, prompt):
        if not _has_key:
            return {"action": "wait", "target": None, "reason": "no_api_key"}

        try:
            res = _client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                timeout=15,
            )
            return json.loads(res.choices[0].message.content)

        except:
            return {"action": "wait", "target": None, "reason": "parse_failed"}

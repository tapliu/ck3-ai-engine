import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class LLM:

    def call(self, prompt):
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}]
            )
            return json.loads(res.choices[0].message.content)

        except:
            return {
                "action":"wait",
                "target":None,
                "reason":"parse_failed"
            }

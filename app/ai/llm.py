# app/ai/llm.py
import os
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

class LLM:

    def call(self, prompt):

        try:
            res = openai.ChatCompletion.create(
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

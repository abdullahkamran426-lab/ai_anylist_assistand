import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    client = None
else:
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=30.0,  # 30 second timeout to prevent hanging
    )

def ask_ai(question, dataset_summary):
    if client is None:
        return "API Key missing. Add OPENROUTER_API_KEY in .env"
        
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct", # Using the affordable paid slug
            max_tokens=500, # Limits tokens to save credits
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Data Analysis Assistant. "
                        "Analyze datasets, explain insights, and provide useful suggestions. "
                        "Keep your answers brief and to the point."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
Dataset Summary:
{dataset_summary}

Question:
{question}

Answer clearly and briefly.
"""
                }
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"AI Error: {e}"
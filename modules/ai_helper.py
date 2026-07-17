"""
AI Helper Module - Natural Language Q&A for Dataset Analysis
==============================================================

This module handles communication with OpenRouter API to provide AI-powered
data analysis assistance. It allows users to ask natural language questions
about their datasets and receive intelligent responses.

Purpose:
--------
- Provides natural language interface for data analysis
- Uses Llama 3.1 8B model via OpenRouter API for affordable AI responses
- Integrates dataset context to provide relevant insights
- Handles API errors gracefully with user-friendly messages

Key Functions:
--------------
- ask_ai(question, dataset_summary): Main function that sends questions to AI
  - Takes user question and dataset summary as input
  - Returns AI-generated response or error message
  - Uses system prompt to guide AI behavior as data analysis assistant

Configuration:
--------------
- Requires OPENROUTER_API_KEY in .env file
- Uses meta-llama/llama-3.1-8b-instruct model (affordable and capable)
- 30 second timeout to prevent hanging
- 500 token limit to control costs
- Temperature 0.3 for focused, deterministic responses

Error Handling:
--------------
- Returns "API Key missing" if no key is configured
- Returns "AI Error: {message}" if API call fails
- Gracefully handles network timeouts and API errors
"""

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

def ask_ai(question, dataset_summary, stream=False):
    if client is None:
        return "API Key missing. Add OPENROUTER_API_KEY in .env"
        
    try:
        messages = [
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
        ]
        
        if stream:
            response = client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct",
                max_tokens=500,
                messages=messages,
                temperature=0.3,
                stream=True
            )
            return response
        else:
            response = client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct",
                max_tokens=500,
                messages=messages,
                temperature=0.3
            )
            return response.choices[0].message.content
        
    except Exception as e:
        if stream:
            # Return an error generator for streaming mode
            def error_generator():
                yield f"AI Error: {e}"
            return error_generator()
        return f"AI Error: {e}"
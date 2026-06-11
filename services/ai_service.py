import os
import asyncio
from typing import AsyncGenerator
import google.generativeai as genai


async def stream_gemini(prompt: str, mode: str, context: str | None, api_key: str) -> AsyncGenerator[bytes, None]:
    """Stream response from Google Generative AI (Gemini). Yields bytes chunks for StreamingResponse."""
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Build system prompt based on mode
    system_prompts = {
        "Doubt Solver": "You are an expert tutor. Answer the student's question clearly and concisely, breaking down complex concepts into understandable parts. Provide step-by-step explanations.",
        "Summarizer": "You are an expert summarizer. Provide a clear, concise summary of the given content in bullet points, highlighting key points and main ideas. Keep it structured and easy to understand.",
        "Quiz Generator": "You are an expert quiz maker. Generate 3-5 multiple choice questions based on the provided content. For each question, provide 4 options (A, B, C, D) and clearly mark the correct answer. Format clearly.",
    }
    
    system_prompt = system_prompts.get(mode, system_prompts["Doubt Solver"])
    
    # Combine context if provided
    full_prompt = f"{system_prompt}\n\n"
    if context:
        full_prompt += f"Content to work with:\n{context}\n\n"
    full_prompt += f"User Request:\n{prompt}"
    
    try:
        # Run the blocking API call in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: model.generate_content(full_prompt, stream=False)
        )
        
        # Yield the response in chunks for streaming effect
        text = response.text if response.text else "No response generated"
        chunk_size = 50
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield chunk.encode("utf-8")
            await asyncio.sleep(0.01)  # Small delay to simulate streaming
            
    except Exception as e:
        yield f"Error: {str(e)}".encode("utf-8")


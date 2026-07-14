import json
import requests
import logging

def generate_research_plan(topic):
    """
    Asks the local AI to classify the topic and generate a structural blueprint 
    and specific search queries to guide the web crawlers.
    """
    logging.info("Calling Local AI to generate a research blueprint for: %s", topic)
    
    system_prompt = (
        "You are an expert Research Planning AI. "
        "Given a topic, determine if it is a 'Person', 'Company', 'Technology', or 'General'. "
        "Create a 15-25 chapter report structure. "
        "Also, generate a list of 10-15 highly specific search queries that a web crawler should use "
        "to find the necessary information to fill those chapters. "
        "CRITICAL: You must reply ONLY with a valid JSON object. No markdown, no conversational text. "
        "Format: {\"category\": \"...\", \"chapters\": [\"...\"], \"search_queries\": [\"...\"]}"
    )
    
    user_prompt = f"Generate the research plan for the topic: {topic}"
    
    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False,
        "format": "json" # Forces Ollama to return clean JSON
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        
        # Parse the JSON directly from the AI's response
        plan = json.loads(response.json().get("response", "{}"))
        logging.info("Blueprint generated! Category: %s", plan.get("category", "Unknown"))
        return plan
        
    except Exception as e:
        logging.error("Failed to generate AI plan: %s", e)
        # Fallback plan if AI fails
        return {
            "category": "General",
            "chapters": ["Introduction", "Background", "Recent News", "Conclusion"],
            "search_queries": [topic, f"{topic} latest news", f"{topic} history"]
        }
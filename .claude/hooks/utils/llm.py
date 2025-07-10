#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai",
#     "python-dotenv",
# ]
# ///

import os
import sys
import random
from dotenv import load_dotenv

load_dotenv()


class LLMManager:
    """Unified LLM manager for enhancing completion messages."""
    
    def __init__(self):
        self.openai_available = bool(os.getenv("OPENAI_API_KEY"))
        
    def enhance_completion_message(self, tool_info: str, engineer_name: str = None) -> str:
        """
        Enhance a tool completion message using LLM or fallback templates.
        
        Args:
            tool_info: Information about what was completed
            engineer_name: Optional engineer name for personalization
            
        Returns:
            str: Enhanced completion message
        """
        # Try LLM enhancement first
        if self.openai_available:
            enhanced = self._enhance_with_openai(tool_info, engineer_name)
            if enhanced:
                return enhanced
        
        # Fallback to template-based enhancement
        return self._enhance_with_template(tool_info, engineer_name)
    
    def _enhance_with_openai(self, tool_info: str, engineer_name: str = None) -> str:
        """Enhance message using OpenAI LLM."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            name_instruction = ""
            if engineer_name:
                name_instruction = f"Sometimes (about 30% of the time) include the engineer's name '{engineer_name}' naturally."
            
            prompt = f"""Create a short, friendly completion message for: {tool_info}

Requirements:
- Keep it under 8 words
- Make it positive and clear
- Use natural, conversational language
- Focus on what was accomplished
- No quotes, formatting, or explanations
- Return ONLY the message text
{name_instruction}

Examples:
- "Completed editing settings.py"
- "Successfully updated 3 todos" 
- "Built project successfully"
- "Razvan, file updated!"

Create ONE completion message:"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7,
            )
            
            message = response.choices[0].message.content.strip()
            message = message.strip().strip('"').strip("'").strip()
            message = message.split("\n")[0].strip()
            
            return message if message else None
            
        except Exception:
            return None
    
    def _enhance_with_template(self, tool_info: str, engineer_name: str = None) -> str:
        """Enhance message using predefined templates."""
        # Simple template enhancement
        if "edited" in tool_info.lower():
            templates = ["Completed editing", "File updated", "Edit successful"]
        elif "wrote" in tool_info.lower():
            templates = ["File created", "Write complete", "New file ready"]
        elif "read" in tool_info.lower():
            templates = ["File read", "Content loaded", "Read complete"]
        elif "ran:" in tool_info.lower():
            templates = ["Command complete", "Task finished", "Execution done"]
        elif "todos" in tool_info.lower():
            templates = ["Todos updated", "Progress tracked", "Tasks organized"]
        else:
            templates = ["Task complete", "Work finished", "All done"]
        
        base_message = random.choice(templates)
        
        # Add personalization occasionally
        if engineer_name and random.random() < 0.3:
            return f"{engineer_name}, {base_message.lower()}"
        
        return base_message


def main():
    """CLI interface for testing."""
    if len(sys.argv) > 1:
        tool_info = " ".join(sys.argv[1:])
        engineer_name = os.getenv('ENGINEER_NAME', '').strip() or None
        
        llm = LLMManager()
        enhanced = llm.enhance_completion_message(tool_info, engineer_name)
        print(enhanced)
    else:
        print("Usage: ./llm.py 'tool completion info'")


if __name__ == "__main__":
    main()
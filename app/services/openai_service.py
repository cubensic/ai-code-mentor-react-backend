from openai import AsyncOpenAI
import yaml
from pathlib import Path
from app.config import settings

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompts = self._load_prompts()
    
    def _load_prompts(self):
        """Load system prompts from YAML file"""
        prompts_path = Path(__file__).parent.parent / "prompts" / "system_prompts.yaml"
        with open(prompts_path, "r") as f:
            return yaml.safe_load(f)
    
    async def stream_response(
        self,
        template_type: str,
        user_message: str,
        files_context: list,
        chat_history: list
    ):
        """Stream AI response with context"""
        system_prompt = self.system_prompts.get(template_type, self.system_prompts["portfolio_website"])
        
        # Build context from files
        context = self._build_context(files_context)
        
        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt + context},
            *chat_history,
            {"role": "user", "content": user_message}
        ]
        
        # Create streaming response
        stream = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            max_tokens=2000,
            temperature=0.7
        )
        
        async def generate():
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield f"data: {delta.content}\n\n"
            yield "data: [DONE]\n\n"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    def _build_context(self, files):
        """Build context string from project files"""
        if not files:
            return ""
        
        context = "\n\nCurrent project files:\n"
        for file in files:
            file_name = file.get("name", "unknown")
            file_type = file.get("file_type", file.get("type", "unknown"))
            file_content = file.get("content", "")
            
            # Limit content to 500 chars per file
            content_preview = file_content[:500] if len(file_content) > 500 else file_content
            
            context += f"\n--- {file_name} ({file_type}) ---\n"
            context += content_preview
            if len(file_content) > 500:
                context += "\n... (truncated)"
        
        return context
    
    def get_initial_message(self, template_type: str) -> str:
        """Get initial greeting message based on template"""
        greetings = {
            "portfolio_website": "Welcome! I'm here to help you build your first portfolio website. Let's start by creating a simple HTML structure. What would you like to add first?",
            "todo_app": "Hello! Ready to build your first interactive Todo app? We'll use HTML for structure, CSS for styling, and JavaScript for functionality. Where would you like to start?",
            "calculator": "Hi there! Let's build a calculator together. We'll create buttons, handle clicks, and perform calculations. What's the first step you'd like to tackle?"
        }
        return greetings.get(template_type, greetings["portfolio_website"])

# Create singleton instance
openai_service = OpenAIService()
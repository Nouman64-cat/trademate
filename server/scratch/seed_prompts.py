from database.database import engine
from models.chatbot_prompt import ChatbotPrompt
from agent.prompts import SYSTEM_PROMPT
from agent.bot import _BOT_SYSTEM_PROMPT
from sqlmodel import Session, select

def seed_prompts():
    with Session(engine) as session:
        # RAG Graph Prompt
        existing_rag = session.exec(select(ChatbotPrompt).where(ChatbotPrompt.name == 'rag_system_prompt')).first()
        if not existing_rag:
            session.add(ChatbotPrompt(
                name='rag_system_prompt', 
                content=SYSTEM_PROMPT, 
                description='System prompt for the simple RAG graph (agent/graph.py)'
            ))
            print("✓ Seeded rag_system_prompt")
        
        # ReAct Agent Prompt
        existing_bot = session.exec(select(ChatbotPrompt).where(ChatbotPrompt.name == 'bot_system_prompt')).first()
        if not existing_bot:
            # _BOT_SYSTEM_PROMPT is a SystemMessage, we want the content string
            content = _BOT_SYSTEM_PROMPT.content
            session.add(ChatbotPrompt(
                name='bot_system_prompt', 
                content=content, 
                description='Core ReAct agent system prompt (agent/bot.py)'
            ))
            print("✓ Seeded bot_system_prompt")
        
        session.commit()

if __name__ == "__main__":
    seed_prompts()

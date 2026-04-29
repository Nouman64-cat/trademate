import logging
from sqlalchemy import text, inspect
from .database import engine

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Simple migration runner to handle schema changes that SQLModel.create_all() 
    doesn't handle (like column type changes or additions to existing tables).
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # --- Migration 1: Ensure otp_codes.used is BOOLEAN ---
    if "otp_codes" in tables:
        columns = inspector.get_columns("otp_codes")
        used_col = next((c for c in columns if c["name"] == "used"), None)
        
        if used_col:
            # In PostgreSQL, VARCHAR(5) shows up as VARCHAR. 
            # We want to make sure it's BOOLEAN.
            type_str = str(used_col["type"]).upper()
            if "VARCHAR" in type_str or "CHAR" in type_str:
                logger.info("Migrating otp_codes.used from %s to BOOLEAN...", type_str)
                try:
                    with engine.connect() as conn:
                        conn.execute(text("ALTER TABLE otp_codes ALTER COLUMN used TYPE BOOLEAN USING used::boolean;"))
                        conn.commit()
                    logger.info("Successfully migrated otp_codes.used to BOOLEAN.")
                except Exception as e:
                    logger.error("Failed to migrate otp_codes.used: %s", e)

    # --- Migration 2: Add is_admin column to users table ---
    if "users" in tables:
        columns = inspector.get_columns("users")
        column_names = [c["name"] for c in columns]

        if "is_admin" not in column_names:
            logger.info("Adding is_admin column to users table...")
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;"))
                    conn.commit()
                logger.info("Successfully added is_admin column to users table.")
            except Exception as e:
                logger.error("Failed to add is_admin column: %s", e)

    # --- Migration 3: Add share_token column to conversations table ---
    if "conversations" in tables:
        columns = inspector.get_columns("conversations")
        column_names = [c["name"] for c in columns]
        if "share_token" not in column_names:
            logger.info("Adding share_token column to conversations table...")
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE conversations ADD COLUMN share_token TEXT UNIQUE;"))
                    conn.commit()
                logger.info("Successfully added share_token column to conversations table.")
            except Exception as e:
                logger.error("Failed to add share_token column: %s", e)

    # --- Migration 4: Add last_login, failed_login_attempts, locked_until to users ---
    if "users" in tables:
        columns = inspector.get_columns("users")
        column_names = [c["name"] for c in columns]

        if "last_login" not in column_names:
            logger.info("Adding last_login column to users table...")
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP;"))
                    conn.commit()
                logger.info("Successfully added last_login column.")
            except Exception as e:
                logger.error("Failed to add last_login column: %s", e)

        if "failed_login_attempts" not in column_names:
            logger.info("Adding failed_login_attempts column to users table...")
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;"))
                    conn.commit()
                logger.info("Successfully added failed_login_attempts column.")
            except Exception as e:
                logger.error("Failed to add failed_login_attempts column: %s", e)

        if "locked_until" not in column_names:
            logger.info("Adding locked_until column to users table...")
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;"))
                    conn.commit()
                logger.info("Successfully added locked_until column.")
            except Exception as e:
                logger.error("Failed to add locked_until column: %s", e)

    # --- Migration 5: Add token-economy columns to messages table ---
    if "messages" in tables:
        columns = inspector.get_columns("messages")
        column_names = [c["name"] for c in columns]
        token_cols = [
            ("prompt_tokens", "INTEGER"),
            ("completion_tokens", "INTEGER"),
            ("model_name", "TEXT"),
            ("cost_usd", "DOUBLE PRECISION"),
        ]
        for col_name, col_type in token_cols:
            if col_name not in column_names:
                logger.info("Adding %s column to messages table...", col_name)
                try:
                    with engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE messages ADD COLUMN {col_name} {col_type};"))
                        conn.commit()
                    logger.info("Successfully added messages.%s.", col_name)
                except Exception as e:
                    logger.error("Failed to add messages.%s: %s", col_name, e)

    # Future migrations can be added here...


def sync_prompts():
    """
    Overwrite the DB-stored bot_system_prompt with the current hardcoded default.
    Called at startup so prompt changes in bot.py take effect without manual DB edits.
    """
    try:
        # Lazy import to avoid circular dependency at module level
        from agent.bot import _BOT_SYSTEM_PROMPT_DEFAULT
        from sqlmodel import Session, select
        from models.chatbot_prompt import ChatbotPrompt

        with Session(engine) as session:
            prompt = session.exec(
                select(ChatbotPrompt).where(ChatbotPrompt.name == "bot_system_prompt")
            ).first()
            if prompt:
                if prompt.content != _BOT_SYSTEM_PROMPT_DEFAULT:
                    prompt.content = _BOT_SYSTEM_PROMPT_DEFAULT
                    session.add(prompt)
                    session.commit()
                    logger.info("bot_system_prompt synced to latest default.")
                else:
                    logger.info("bot_system_prompt already up to date.")
            else:
                session.add(ChatbotPrompt(
                    name="bot_system_prompt",
                    content=_BOT_SYSTEM_PROMPT_DEFAULT,
                    description="Core ReAct agent system prompt (agent/bot.py)",
                ))
                session.commit()
                logger.info("bot_system_prompt inserted into DB.")
    except Exception as exc:
        logger.error("sync_prompts failed: %s", exc)

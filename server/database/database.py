import os
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def create_db_tables():
    # Import all models here so SQLModel picks them up before create_all
    import models.user  # noqa: F401
    import models.conversation  # noqa: F401
    import models.otp  # noqa: F401
    import models.interaction  # noqa: F401
    import models.recommendation  # noqa: F401
    import models.user_preference  # noqa: F401
    import models.route_evaluation_history  # noqa: F401
    import models.model_metadata  # noqa: F401
    import models.ab_test  # noqa: F401
    import models.freightos_rate  # noqa: F401
    SQLModel.metadata.create_all(engine)
    
    # Run manual migrations for schema changes not handled by create_all
    from .migrations import run_migrations, sync_prompts
    run_migrations()
    sync_prompts()

    # Clear compiled agent cache so any prompt change takes effect immediately
    try:
        from agent.bot import clear_agent_cache
        clear_agent_cache()
    except Exception:
        pass



def get_session():
    with Session(engine) as session:
        yield session

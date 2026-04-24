from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 1. Create the Engine
# pool_pre_ping=True is a crucial production setting. 
# It checks if the database connection is still alive before using it, 
# preventing "MySQL server has gone away" style errors in Postgres.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True,)

# 2. Create the Session Local class
# autoflush=False prevents SQLAlchemy from prematurely sending data to the DB 
# before we explicitly call commit().
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. The Dependency Injection function
# This is where FastAPI shines. We will "inject" this function into our routes.
def get_db():
    """Dependency that provides a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
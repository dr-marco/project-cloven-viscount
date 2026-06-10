from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from contextlib import asynccontextmanager
from langchain.globals import set_debug
from sqlalchemy import text

# Local imports
from routes import router, limiter
from database import async_session_maker

# DEBUG flag
set_debug(False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP (Warmup) ---
    print("🚀 Server initialization - Starting Warmup...")
    
    try:
        # Postgres health check
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        print("✅ DB Health Check: PostgreSQL is reachable and operational.")
    except Exception as e:
        print(f"❌ DB Health Check CRITICAL: unable to connect to PostgreSQL: {e}")
    
    print("💡 Vector Store: ChromaDB connection postponed to runtime (Lazy Loading).")
    print("🟢 API Gateway ready to listen on port 8000.")
    
    yield
    
    # --- SHUTDOWN ---
    print("🛑 Server shutdown in progress... Releasing resources")
app = FastAPI(
    title="Cloven Viscount API",
    lifespan=lifespan
)

# Rate Limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include the decoupled routes
app.include_router(router)
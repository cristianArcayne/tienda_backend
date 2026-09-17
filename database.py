import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Configuración de URL de conexión a base de datos
# Si existe variable de entorno DATABASE_URL la utiliza; de lo contrario usa SQLite local
DEFAULT_DB_URL = "sqlite:///./fashionstore.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Si se configuró PostgreSQL pero no está instalado psycopg2 localmente, fallback a SQLite
if DATABASE_URL.startswith("postgresql"):
    try:
        import psycopg2
    except ImportError:
        DATABASE_URL = DEFAULT_DB_URL

# Configuración de connect_args para SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Generador de dependencias de sesión de base de datos para FastAPI.
    Garantiza que la sesión siempre se cierre al finalizar la petición HTTP.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

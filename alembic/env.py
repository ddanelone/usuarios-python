from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.ext.asyncio import async_engine_from_config

from dotenv import load_dotenv

from app.db.base import Base
from app.db.models import user  # Importa todos los modelos
target_metadata = Base.metadata

# Cargar variables de entorno
load_dotenv()

# Importar Base y modelos
from app.db.base import Base
from app.db.models.user import User

# Configuración de Alembic
config = context.config

# ✔️ Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✔️ DATABASE_URL segura
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Falta la variable DATABASE_URL en el entorno")

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Metadatos de los modelos
target_metadata = Base.metadata

# (El resto del archivo sigue igual...)

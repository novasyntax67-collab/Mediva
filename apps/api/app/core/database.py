import sys
import os

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from database.session import engine, async_session_maker, get_db_session as get_db
from database.models import Base

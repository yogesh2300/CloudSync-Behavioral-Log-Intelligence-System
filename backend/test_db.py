from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
        print("✅ Connected Successfully!")
        print(version)
except Exception as e:
    print("❌ Connection Failed")
    print(e)
from core.config import local_session

def get_db_connection():
    db = local_session()
    try:
        yield db
    finally:
        db.close()


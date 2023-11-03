from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import sessionmaker

from app.core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_TESTING_DATABASE_URI), pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

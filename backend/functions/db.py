from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.config import config

def get_database_url():
    """
    Construct the SQLAlchemy database URL based on the configuration.
    """
    if config.DB_TYPE == 'test':
        return "sqlite:///tests/test.db"
    elif config.DB_TYPE == 'mysql':
        return f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT or 3306}/{config.DB_NAME}"
    elif config.DB_TYPE == 'postgres':
        return f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT or 5432}/{config.DB_NAME}"
    elif config.DB_TYPE == 'sqlite':
        return f"sqlite:///{config.DB_NAME}.db"
    else:
        raise ValueError(f"Unsupported DB_TYPE: {config.DB_TYPE}")

def get_engine():
    database_url = get_database_url()
    return create_engine(database_url)

def get_session():
    """
    Provides a new database session (connection).
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
# create_tables.py
import sys
import os
import logging
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_tables.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_path():
    """Add the parent directory to sys.path to allow absolute imports."""
    try:
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
        sys.path.insert(0, parent_dir)
        logger.debug(f"Added {parent_dir} to Python path")
        return True
    except Exception as e:
        logger.error(f"Failed to set up Python path: {str(e)}")
        return False

def import_models():
    """Import database models and engine."""
    try:
        # First try to import from the app module
        from app.database import Base, engine, User
        logger.info("Successfully imported database models")
        return Base, engine
    except ImportError as ie:
        logger.error(f"Import error: {str(ie)}")
        logger.error("Make sure you're running this script from the project root directory")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error importing models: {str(e)}")
        return None, None

def create_tables(Base, engine):
    """Create all tables defined in the models."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Available tables: {', '.join(tables)}")
        
        return True
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating tables: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating tables: {str(e)}")
        return False

def main():
    """Main function to create database tables."""
    try:
        logger.info("Starting table creation process")
        
        # Set up path for imports
        if not setup_path():
            return False
            
        # Import database models
        Base, engine = import_models()
        if not Base or not engine:
            return False
            
        # Create tables
        if create_tables(Base, engine):
            logger.info("Table creation complete!")
            logger.info("Now you can run 'python -m app.main' to start the application")
            return True
        else:
            logger.error("Table creation failed")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during table creation: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
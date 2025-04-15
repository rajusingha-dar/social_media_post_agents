# setup_db.py
import mysql.connector
from mysql.connector import errorcode
import os
import logging
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_setup.log')
    ]
)
logger = logging.getLogger(__name__)

def load_environment_variables():
    """Load environment variables from .env file."""
    try:
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
        return True
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return False

def get_db_config():
    """Get database configuration from environment variables."""
    try:
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '3306'),
        }
        db_name = os.getenv('DB_NAME', 'ai_social_poster')
        
        # Log configuration (but mask password)
        log_config = config.copy()
        if log_config['password']:
            log_config['password'] = '********'
        logger.info(f"Database configuration: {log_config}, DB_NAME: {db_name}")
        
        return config, db_name
    except Exception as e:
        logger.error(f"Error retrieving database config: {str(e)}")
        return None, None

def create_database(config, db_name):
    """Create the database if it doesn't exist."""
    cnx = None
    try:
        logger.info(f"Connecting to MySQL server at {config['host']}:{config['port']}")
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
        # Try to create database if it doesn't exist
        try:
            logger.info(f"Creating database '{db_name}' if it doesn't exist")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            logger.info(f"Database '{db_name}' created successfully")
        except mysql.connector.Error as err:
            logger.error(f"Failed creating database: {err}")
            return False
            
        # Test database connection
        try:
            logger.info(f"Testing connection to database '{db_name}'")
            cursor.execute(f"USE {db_name}")
            logger.info(f"Successfully connected to database '{db_name}'")
        except mysql.connector.Error as err:
            logger.error(f"Failed to connect to database: {err}")
            return False
            
        cursor.close()
        return True
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Error: Access denied. Check your username and password.")
        else:
            logger.error(f"Error: {err}")
        return False
    finally:
        if cnx is not None and cnx.is_connected():
            cnx.close()
            logger.debug("Database connection closed")

def main():
    """Main function to set up the database."""
    try:
        logger.info("Starting database setup process")
        
        # Load environment variables
        if not load_environment_variables():
            logger.warning("Continuing with default environment variables")
        
        # Get database configuration
        config, db_name = get_db_config()
        if not config or not db_name:
            logger.error("Failed to get database configuration")
            sys.exit(1)
        
        # Create database
        if create_database(config, db_name):
            logger.info("Database setup complete!")
            logger.info("Now you can run 'python create_tables.py' to create tables")
            logger.info("Then run 'python -m app.main' to start the application")
            return True
        else:
            logger.error("Database setup failed")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during database setup: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
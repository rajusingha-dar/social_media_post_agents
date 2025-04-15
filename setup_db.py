# setup_db.py
import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '3306'),
}

DB_NAME = os.getenv('DB_NAME', 'ai_social_poster')

def create_database():
    """Create the database if it doesn't exist."""
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
        # Try to create database if it doesn't exist
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
            print(f"Database '{DB_NAME}' created successfully.")
        except mysql.connector.Error as err:
            print(f"Failed creating database: {err}")
            exit(1)
            
        cursor.close()
        cnx.close()
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Access denied. Check your username and password.")
        else:
            print(f"Error: {err}")
        exit(1)

def main():
    """Main function to set up the database."""
    create_database()
    print("Database setup complete!")
    print("Now you can run 'python -m app.main' to start the application.")

if __name__ == "__main__":
    main()
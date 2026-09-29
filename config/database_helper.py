from dotenv import load_dotenv

import os
from pathlib import Path
import sqlite3


class database:

    load_dotenv()

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATABASE_DIR = BASE_DIR / "database"

    @classmethod
    def get_connection(cls, database_name):
        database_path = cls.DATABASE_DIR / database_name
        return sqlite3.connect(database_path)

    @classmethod
    def create_database(cls):
        database_name = os.getenv("DATABASE_NAME")

        try:
            connection = cls.get_connection(database_name)
            connection.close()
            return True
        except:
            return False
        
    @classmethod
    def get_database_name(cls):
        return os.getenv("DATABASE_NAME")
    
    @classmethod
    def create_table(cls,queries):
        database_name = os.getenv("DATABASE_NAME")
        try:
            with cls.get_connection(database_name) as connection:
                for query in queries:
                    connection.execute(query)
        finally:
            connection.close()            

    @classmethod
    def check_system_id(cls, query, system_id):
        database_name = os.getenv("DATABASE_NAME")
        try:
            with cls.get_connection(database_name) as connection:
                cursor = connection.cursor()

                cursor.execute(query, (system_id,))
                result = cursor.fetchone()

                return result is not None
        finally:
            connection.close()    


    @classmethod
    def add_system_or_log(cls, query, *args):
        database_name = cls.get_database_name()
        try:
            
            with cls.get_connection(database_name) as connection:
                connection.execute(query,args)
                connection.commit()
                return True
        except sqlite3.Error as e:
            print("SQLite Error:", e)
            return False
        finally:
            connection.close()


    @classmethod
    def get_all_user_profiles(cls, query):
        database_name = cls.get_database_name()
        try:
            with cls.get_connection(database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(query)
                users = cursor.fetchall()
                return users

        finally:
            connection.close()

    @classmethod
    def get_all_data_of_user(cls,query,**args):
        database_name = cls.get_database_name()
        try:
            with cls.get_connection(database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(query,(args.get("user_id"),))
                results = cursor.fetchall()

                return results

        finally:
            connection.close()              




        
            
from config.database_query_helper import QueriesHelper as qh
from config.database_helper import database
from manager.manager import Manager
from voice.echo_speak import Speech

from core.core_helper import sort_users, check_for_user
import queue
import threading
import time

class echo_data:

    def __init__(self,manager):
        self.lock = threading.RLock()

        self.all_user_profiles = self.get_all_user_profiles()
        self.manager = manager
        # Infront of camera
        self.latest_embeddings = queue.Queue()
        self.latest_emotions = None
        # Update from latest embedding
        self.current_user = None
        self.current_user_emotion = None

        self.running = True


        self.user_not_found = True
        self.user_provided_data = False

        self.user_is_concerned = None

    def get_all_user_profiles(self):

        users = database.get_all_user_profiles(qh.GET_ALL_USER_PROFILES)

        return sort_users(users)

    def start_updating(self):
        
        while self.running:

            embedding = self.latest_embeddings.get()

            if self.user_is_concerned is not None:

                for i in self.user_is_concerned:
                    concern_embedding = i[0]
                    concern_name = i[1]

            result = check_for_user(self.all_user_profiles,embedding)

            if result == "no users found":

                data = {
                    "task" : "no user found"
                }

                self.manager.user_input.put(data)

                while self.user_not_found:

                    time.sleep(2)

                if self.user_provided_data:
                    
                # user denied giving details save that user embedding as unknown with id and update current catch and database    



                 
    def add_user_embedding(self):
        print()


    def add_camera_data(self,embeddings, emotions):
        with self.lock:
            self.latest_embeddings.put(embeddings)
            self.latest_emotions = emotions

    def stop(self):
        self.running = False        




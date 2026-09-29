from config.system_helper import helper_main
from api.echo_api import start_server
from api.echo_api import send_frontend_event
from manager.manager import Manager
from Camera.camera import Camera
from core.cental_hub import echo_data
from voice.echo_speak import Speech
from Hearing.wake_word import WakeWordListener
from brain.brain_classifier import Classifier
import time
import threading
import queue


def start_all_threads(manager):

        try:

            speech = Speech()
            
            speech_thread = threading.Thread(
                    target=speech.start_speech,
                    name="EchoTTSThread",
                    daemon=True
                )

            speech_thread.start()


            wake_word = WakeWordListener()
            
            wake_word_thread = threading.Thread(
                    target=wake_word.start,
                    daemon=True
                )
            
            wake_word_thread.start()


            echo_hub = echo_data(manager)
                
            hub_thread = threading.Thread(
                        target = echo_hub.start_updating,
                        name = "ECHO-DATA-HUB",
                        daemon= True
                    )
                
            hub_thread.start()


            camera = Camera(echo_hub)
            
            camera_thread = threading.Thread(
                    target=camera.start,
                    name="ECHO-Camera",
                    daemon=True
                )
            
            camera_thread.start()

            classifier = Classifier(manager,speech)

            classifier_thread = threading.Thread(
                target=classifier.start,
                name="ECHO-Gemma-Classifier",
                daemon=True
            )

            classifier_thread.start()

            return {
                "speech": speech,
                "wake_word": wake_word,
                "echo_hub": echo_hub,
                "camera": camera,
                "brain" : classifier,

                "speech_thread": speech_thread,
                "wake_word_thread": wake_word_thread,
                "hub_thread": hub_thread,
                "camera_thread": camera_thread,
                "brain_thread" : classifier_thread
            }
        
        except:
            speech.stop_speech()
            wake_word.stop()
            echo_hub.stop()
            camera.stop()
            classifier.stop()
            return False, None, None, None, None, None

            
def main():
    result = helper_main()

    if not result:
        print("There is a Problem in setup") 

    server_started = start_server()

    if not server_started:
        print("Unable to start ECHO frontend.")   

    print("ECHO frontend started.")

    manager = Manager()
    workers = start_all_threads(manager)

    try:
            manager_thread = threading.Thread(
                target = manager.manager_start(workers["speech"], workers["wake_word"], workers["echo_hub"], workers["camera"], workers["brain"]),
                name = "Manager_thread",
                daemon = True
            )

            manager_thread.start()

    except:
        manager.manager_stop()       

    echo_shutdown_message = queue.Queue()

    try:

        while True:
            
            message = echo_shutdown_message.get()

            if message == "shut down":
                shut_down_echo(workers,manager, manager_thread)

    except KeyboardInterrupt:
        shut_down_echo(workers,manager, manager_thread)
           

def shut_down_echo(workers, manager, manager_thread):

    print("\nShutting down ECHO...")
     
    manager.manager_stop()
     
    workers["speech"].stop_speech()
     
    workers["wake_word"].stop()
     
    workers["echo_hub"].stop()
     
    workers["camera"].stop()
     
     
    workers["speech_thread"].join(timeout=5)
     
    workers["wake_word_thread"].join(timeout=5)
     
    workers["hub_thread"].join(timeout=5)
     
    workers["camera_thread"].join(timeout=5)
     
    manager_thread.join(timeout=5)

if __name__ == "__main__":

    main()
    
        
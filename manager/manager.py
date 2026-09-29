from manager.manager_helper import take_user_concern
import queue

class Manager:

    def __init__(self):
        self.is_running = True
        self.user_input = queue.Queue()
        self.unknown_face_detected = False
        self.help_required = queue.Queue()
        self.speak = None
        self.wake_word = None
        self.echo_hub = None
        self.camera = None 
        self.brain = None     
    
    def manager_stop(self):

        self.is_running = False

    
    def manager_start(self, speech, wake_word, echo_hub, camera, brain):

        self.speak = speech
        self.wake_word = wake_word
        self.echo_hub = echo_hub
        self.camera = camera
        self.brain = brain

        while self.is_running:

            echo_input = self.user_input.get()

            if echo_input["task"] == "start primary user pairing":
                #start pairing
                print(echo_input)

            elif echo_input["task"] == "no user found":

                self.camera.dont_add_embeddings = True
                
                self.speak.speak("Hey! It looks like we're meeting for the first time. "
                                    "I'd love to get to know you better. "
                                    "If you're comfortable sharing a few details about yourself, just follow the instructions on the screen."
                                    )
                concern_result = take_user_concern(self.speak)
                
                if concern_result == "denied":
                    
                    # update variable of camera class and also hub class
                    self.echo_hub.no_user_found = False

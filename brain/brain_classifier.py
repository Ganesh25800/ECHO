from llama_cpp import Llama
import queue


class Classifier:

    def __init__(self, manager, speech):

        self.manager = manager
        self.speech = speech

        self.running = True

        self.input_queue = queue.Queue()

        self.model = None

        self.model_path = "models/classifier/gemma-3-1b-it-Q4_K_M.gguf"


    def load_model(self):

        print("Loading ECHO Gemma classifier...")

        self.model = Llama(
            model_path=self.model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=-1,
            verbose=False
        )

        print("ECHO Gemma classifier loaded.")


    def start(self):

        try:

            self.load_model()

            while self.running:

                data = self.input_queue.get()

                if data is None:
                    break

                self.process(data)

        except Exception as error:

            print(f"ECHO Gemma classifier error: {error}")

        finally:

            print("ECHO Gemma classifier stopped.")


    def process(self, data):

        user_text = data.get("text")

        if not user_text:
            return


        messages = [
            {
                "role": "system",
                "content": "You are ECHO, a personal AI assistant."
            },
            {
                "role": "user",
                "content": user_text
            }
        ]


        stream = self.model.create_chat_completion(
            messages=messages,
            max_tokens=512,
            temperature=0.7,
            stream=True
        )


        full_response = ""

        speech_buffer = ""


        for chunk in stream:

            if not self.running:
                break


            delta = chunk["choices"][0]["delta"]

            token = delta.get("content")

            if not token:
                continue


            full_response += token

            speech_buffer += token


            if self.should_speak(speech_buffer):

                text_to_speak = speech_buffer.strip()

                if text_to_speak:

                    self.speech.speak(
                        text_to_speak
                    )

                speech_buffer = ""


        if speech_buffer.strip():

            self.speech.speak(
                speech_buffer.strip()
            )


        result = {
            "task": "gemma response",
            "response": full_response.strip()
        }

        self.manager.user_input.put(
            result
        )


    def should_speak(self, text):

        text = text.rstrip()

        if not text:
            return False

        if text[-1] in [".", "!", "?", ";", ":"]:
            return True

        return False


    def add_input(self, data):

        self.input_queue.put(
            data
        )


    def stop(self):

        self.running = False

        self.input_queue.put(
            None
        )
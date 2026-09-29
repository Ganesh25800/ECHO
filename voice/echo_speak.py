import json
import queue
import threading
from pathlib import Path

import sounddevice as sd
from kokoro_onnx import Kokoro
from api.echo_api import send_frontend_event


class Speech:

    def __init__(self):

        self.base_dir = Path(__file__).resolve().parent.parent

        self.emotion_file = (
            self.base_dir
            / "json"
            / "echo_temp_emotions.json"
        )

        # Kokoro model files
        self.kokoro_model_path = (
            self.base_dir
            / "models"
            / "kokoro"
            / "kokoro-v1.0.onnx"
        )

        self.kokoro_voices_path = (
            self.base_dir
            / "models"
            / "kokoro"
            / "voices-v1.0.bin"
        )

        self.speak_queue = queue.Queue()

        self.running = False

        self.emotion_lock = threading.Lock()

        self.kokoro = None

        # Default voice
        self.voice = "af_heart"

        # American English
        self.language = "en-us"

        self.happy = 0.0
        self.sad = 0.0
        self.anger = 0.0
        self.confused = 0.0
        self.frustrated = 0.0

        self.calm = 0.0
        self.excited = 0.0
        self.concerned = 0.0
        self.empathetic = 0.0
        self.neutral = 1.0

        # ============================================================
        # EMOTIONAL DIMENSIONS
        # ============================================================

        self.valence = 0.0
        self.arousal = 0.0
        self.dominance = 0.0


        # ============================================================
        # VOICE / PROSODY PARAMETERS
        # ============================================================

        self.pitch = 1.0
        self.pitch_variation = 0.5

        self.speed = 0.8
        self.energy = 1.0
        self.volume = 1.0

        self.breathiness = 0.5
        self.tension = 0.0
        self.warmth = 0.5

        self.pause_frequency = 0.5
        self.pause_duration = 0.9

        self.rhythm_variation = 0.8
        self.emphasis = 0.5


        # ============================================================
        # LOAD INITIAL EMOTION STATE
        # ============================================================

        self.load_emotion_state()


    # ================================================================
    # LOAD KOKORO
    # ================================================================

    def load_kokoro(self):

        # Already loaded
        if self.kokoro is not None:
            return True

        try:

            if not self.kokoro_model_path.is_file():

                print(
                    "Kokoro model not found:"
                )

                print(
                    self.kokoro_model_path
                )

                return False


            if not self.kokoro_voices_path.is_file():

                print(
                    "Kokoro voices file not found:"
                )

                print(
                    self.kokoro_voices_path
                )

                return False


            print(
                "Loading ECHO Kokoro voice engine..."
            )


            self.kokoro = Kokoro(
                str(self.kokoro_model_path),
                str(self.kokoro_voices_path)
            )


            print(
                "ECHO Kokoro voice engine loaded."
            )


            return True


        except Exception as error:

            print(
                f"Unable to load Kokoro: {error}"
            )

            self.kokoro = None

            return False
        

    def load_emotion_state(self):

        if not self.emotion_file.is_file():
            print("Emotion JSON file not found.")
            return

        try:
            with open(self.emotion_file,"r") as file:
                data = json.load(file)

            with self.emotion_lock:
                self.happy = data.get("happy",self.happy)

                self.sad = data.get("sad",self.sad)

                self.anger = data.get("anger",self.anger)

                self.confused = data.get("confused",self.confused)

                self.frustrated = data.get("frustrated",self.frustrated)

                self.calm = data.get("calm",self.calm)

                self.excited = data.get("excited",self.excited)

                self.concerned = data.get("concerned",self.concerned)

                self.empathetic = data.get("empathetic",self.empathetic)

                self.neutral = data.get("neutral",self.neutral)

        except (json.JSONDecodeError,OSError) as error:

            print(f"Unable to load emotion state: {error}")


    # ================================================================
    # UPDATE EMOTION
    # ================================================================

    def update_emotion(self,emotion_name,value):

        value = max(
            0.0,
            min(
                1.0,
                float(value)
            )
        )


        with self.emotion_lock:

            if hasattr(
                self,
                emotion_name
            ):

                setattr(
                    self,
                    emotion_name,
                    value
                )

    #add speak to queue

    def speak(self,text):

        if not text:
            return

        text = str(text).strip()

        if not text:
            return

        self.speak_queue.put(text)


    # ================================================================
    # CALCULATE CURRENT EMOTION
    # ================================================================

    def calculate_emotion(self):

        with self.emotion_lock:

            emotions = {

                "happy":
                    self.happy,

                "sad":
                    self.sad,

                "anger":
                    self.anger,

                "confused":
                    self.confused,

                "frustrated":
                    self.frustrated,

                "calm":
                    self.calm,

                "excited":
                    self.excited,

                "concerned":
                    self.concerned,

                "empathetic":
                    self.empathetic,

                "neutral":
                    self.neutral
            }


            primary_emotion = max(
                emotions,
                key=emotions.get
            )


            intensity = emotions[
                primary_emotion
            ]


            return {

                "primary_emotion":
                    primary_emotion,

                "intensity":
                    intensity,

                "emotions":
                    emotions
            }


    # ================================================================
    # CALCULATE SPEECH PARAMETERS
    # ================================================================

    def calculate_speech_parameters(self):

        emotion = (
            self.calculate_emotion()
        )


        primary = emotion[
            "primary_emotion"
        ]

        intensity = emotion[
            "intensity"
        ]


        # ------------------------------------------------------------
        # DEFAULT / NEUTRAL BASELINE
        # ------------------------------------------------------------

        pitch = 1.0

        pitch_variation = 0.5

        speed = 1.0

        energy = 0.5

        volume = 1.0

        breathiness = 0.0

        tension = 0.0

        warmth = 0.5

        pause_frequency = 0.3

        pause_duration = 0.3

        rhythm_variation = 0.5

        emphasis = 0.5


        # ------------------------------------------------------------
        # HAPPY
        # ------------------------------------------------------------

        if primary == "happy":

            pitch += (
                0.08 * intensity
            )

            pitch_variation += (
                0.15 * intensity
            )

            speed += (
                0.08 * intensity
            )

            energy += (
                0.30 * intensity
            )

            warmth += (
                0.25 * intensity
            )

            rhythm_variation += (
                0.10 * intensity
            )


        # ------------------------------------------------------------
        # SAD
        # ------------------------------------------------------------

        elif primary == "sad":

            pitch -= (
                0.08 * intensity
            )

            pitch_variation -= (
                0.10 * intensity
            )

            speed -= (
                0.15 * intensity
            )

            energy -= (
                0.25 * intensity
            )

            volume -= (
                0.10 * intensity
            )

            breathiness += (
                0.20 * intensity
            )

            pause_frequency += (
                0.15 * intensity
            )

            pause_duration += (
                0.20 * intensity
            )


        # ------------------------------------------------------------
        # ANGER
        # ------------------------------------------------------------

        elif primary == "anger":

            pitch += (
                0.05 * intensity
            )

            speed += (
                0.08 * intensity
            )

            energy += (
                0.40 * intensity
            )

            volume += (
                0.10 * intensity
            )

            tension += (
                0.60 * intensity
            )

            emphasis += (
                0.25 * intensity
            )


        # ------------------------------------------------------------
        # CONFUSED
        # ------------------------------------------------------------

        elif primary == "confused":

            pitch += (
                0.03 * intensity
            )

            pitch_variation += (
                0.15 * intensity
            )

            speed -= (
                0.10 * intensity
            )

            pause_frequency += (
                0.20 * intensity
            )

            rhythm_variation += (
                0.20 * intensity
            )


        # ------------------------------------------------------------
        # FRUSTRATED
        # ------------------------------------------------------------

        elif primary == "frustrated":

            speed += (
                0.03 * intensity
            )

            energy += (
                0.20 * intensity
            )

            tension += (
                0.40 * intensity
            )

            emphasis += (
                0.20 * intensity
            )


        # ------------------------------------------------------------
        # CALM
        # ------------------------------------------------------------

        elif primary == "calm":

            pitch_variation -= (
                0.10 * intensity
            )

            speed -= (
                0.08 * intensity
            )

            energy -= (
                0.10 * intensity
            )

            warmth += (
                0.20 * intensity
            )

            tension -= (
                0.10 * intensity
            )

            pause_duration += (
                0.10 * intensity
            )


        # ------------------------------------------------------------
        # EXCITED
        # ------------------------------------------------------------

        elif primary == "excited":

            pitch += (
                0.12 * intensity
            )

            pitch_variation += (
                0.20 * intensity
            )

            speed += (
                0.12 * intensity
            )

            energy += (
                0.40 * intensity
            )

            emphasis += (
                0.20 * intensity
            )

            rhythm_variation += (
                0.15 * intensity
            )


        # ------------------------------------------------------------
        # CONCERNED
        # ------------------------------------------------------------

        elif primary == "concerned":

            speed -= (
                0.08 * intensity
            )

            warmth += (
                0.20 * intensity
            )

            tension += (
                0.10 * intensity
            )

            pause_frequency += (
                0.10 * intensity
            )


        # ------------------------------------------------------------
        # EMPATHETIC
        # ------------------------------------------------------------

        elif primary == "empathetic":

            pitch -= (
                0.03 * intensity
            )

            speed -= (
                0.08 * intensity
            )

            energy -= (
                0.05 * intensity
            )

            warmth += (
                0.40 * intensity
            )

            breathiness += (
                0.10 * intensity
            )

            pause_duration += (
                0.10 * intensity
            )


        # ------------------------------------------------------------
        # CLAMP VALUES
        # ------------------------------------------------------------

        pitch = max(
            0.5,
            min(
                1.5,
                pitch
            )
        )

        pitch_variation = max(
            0.0,
            min(
                1.0,
                pitch_variation
            )
        )

        speed = max(
            0.70,
            min(
                1.30,
                speed
            )
        )

        energy = max(
            0.0,
            min(
                1.0,
                energy
            )
        )

        volume = max(
            0.0,
            min(
                1.0,
                volume
            )
        )

        breathiness = max(
            0.0,
            min(
                1.0,
                breathiness
            )
        )

        tension = max(
            0.0,
            min(
                1.0,
                tension
            )
        )

        warmth = max(
            0.0,
            min(
                1.0,
                warmth
            )
        )

        pause_frequency = max(
            0.0,
            min(
                1.0,
                pause_frequency
            )
        )

        pause_duration = max(
            0.0,
            min(
                1.0,
                pause_duration
            )
        )

        rhythm_variation = max(
            0.0,
            min(
                1.0,
                rhythm_variation
            )
        )

        emphasis = max(
            0.0,
            min(
                1.0,
                emphasis
            )
        )


        # ------------------------------------------------------------
        # UPDATE CURRENT STATE
        # ------------------------------------------------------------

        self.pitch = pitch

        self.pitch_variation = (
            pitch_variation
        )

        self.speed = speed

        self.energy = energy

        self.volume = volume

        self.breathiness = (
            breathiness
        )

        self.tension = tension

        self.warmth = warmth

        self.pause_frequency = (
            pause_frequency
        )

        self.pause_duration = (
            pause_duration
        )

        self.rhythm_variation = (
            rhythm_variation
        )

        self.emphasis = emphasis


        return {

            "emotion":
                primary,

            "intensity":
                intensity,

            "pitch":
                self.pitch,

            "pitch_variation":
                self.pitch_variation,

            "speed":
                self.speed,

            "energy":
                self.energy,

            "volume":
                self.volume,

            "breathiness":
                self.breathiness,

            "tension":
                self.tension,

            "warmth":
                self.warmth,

            "pause_frequency":
                self.pause_frequency,

            "pause_duration":
                self.pause_duration,

            "rhythm_variation":
                self.rhythm_variation,

            "emphasis":
                self.emphasis
        }


    # ================================================================
    # GENERATE AND PLAY SPEECH
    # ================================================================

    def generate_speech(self,text,parameters):

        if self.kokoro is None:
            loaded = (self.load_kokoro())

            if not loaded:
                return
            
        try:
            # ========================================================
            # GENERATE AUDIO DIRECTLY INTO MEMORY
            # ========================================================

            samples, sample_rate = (
                    self.kokoro.create(
                    text,
                    voice=self.voice,
                    speed=parameters[
                        "speed"
                    ],
                    lang=self.language
                )
            )


            # ========================================================
            # APPLY OUTPUT VOLUME
            # ========================================================

            samples = (samples * parameters["volume"])

            send_frontend_event("TTS_STARTED")
            # ========================================================
            # PLAY DIRECTLY FROM MEMORY
            # ========================================================
            try:
                sd.play(samples,sample_rate)


            # Wait until ECHO finishes speaking before processing
            # the next item in the speech queue.
                sd.wait()


            # Nothing is saved.
            #
            # samples only exists in memory during this method.
            # After this method returns, Python can release it.
            finally:
                send_frontend_event("TTS_FINISHED")

        except Exception as error:

            print(f"TTS generation/playback error: {error}")


    # ================================================================
    # SPEECH WORKER
    # ================================================================

    def start_speech(self):

        if self.running:
            return

        self.running = True


        print("ECHO Speech Engine started.")


        # Load Kokoro once when speech engine starts.
        #
        # We DO NOT want to reload the ONNX model every time
        # ECHO speaks.

        if not self.load_kokoro():

            self.running = False
            return

        while self.running:

            # --------------------------------------------------------
            # WAIT FOR SPEECH
            # --------------------------------------------------------

            text = (self.speak_queue.get())

            # --------------------------------------------------------
            # STOP SIGNAL
            # --------------------------------------------------------

            if text is None:

                self.speak_queue.task_done()
                break

            try:

                # ----------------------------------------------------
                # GET CURRENT EMOTION / SPEECH PARAMETERS
                # ----------------------------------------------------
                parameters = (self.calculate_speech_parameters())

                # ----------------------------------------------------
                # GENERATE + PLAY SPEECH
                # ----------------------------------------------------

                self.generate_speech(
                    text,
                    parameters
                )


            except Exception as error:

                print(f"Speech error: {error}")


            finally:

                self.speak_queue.task_done()


        self.running = False


        print(
            "ECHO Speech Engine stopped."
        )


    # ================================================================
    # STOP SPEECH ENGINE
    # ================================================================

    def stop_speech(self):

        if not self.running:
            return


        self.running = False


        # Stop any audio currently playing
        try:

            sd.stop()

        except Exception:

            pass


        # Wake Queue.get()
        self.speak_queue.put(
            None
        )
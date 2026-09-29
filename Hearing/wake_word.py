import queue
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from openwakeword.model import Model
from api.echo_api import send_frontend_event


class WakeWordListener:

    def __init__(self):

        self.base_dir = Path(__file__).resolve().parent.parent
        self.wake_model_path = self.base_dir / "models" / "wake_word" / "hey_echo.onnx"
        self.whisper_model_path = self.base_dir / "models" / "whisper"

        self.sample_rate = 16000
        self.chunk_size = 1280
        self.channels = 1

        self.wake_threshold = 0.50
        self.silence_threshold = 350
        self.silence_duration = 1.5
        self.max_recording_duration = 30

        self.listening_cooldown = 5

        self.audio_queue = queue.Queue()
        self.running = False

        # Models load immediately when the object is created
        self.wake_model = self._load_wake_model()
        self.whisper_model = self._load_whisper_model()

    # =========================================================
    # MODEL LOADING (happens at construction time)
    # =========================================================

    def _load_wake_model(self):
        wake_word_dir = self.wake_model_path.parent
        melspec_path = wake_word_dir / "melspectrogram.onnx"
        embedding_path = wake_word_dir / "embedding_model.onnx"

        for path in (self.wake_model_path, melspec_path, embedding_path):
            if not path.exists():
                raise FileNotFoundError(
                    f"Required wake word file not found: {path}"
                )

        print("Loading Hey ECHO model...")

        model = Model(
            wakeword_models=[str(self.wake_model_path)],
            melspec_model_path=str(melspec_path),
            embedding_model_path=str(embedding_path),
            inference_framework="onnx"
        )

        print("Hey ECHO model loaded.")

        return model

    def _load_whisper_model(self):
        print("Loading Whisper...")

        model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
            download_root=str(self.whisper_model_path)
        )

        print("Whisper loaded.")

        return model

    # =========================================================
    # START WAKE WORD LISTENER
    # This is a normal method.
    # The thread will be created outside this class.
    # =========================================================

    def start(self):
        self.running = True

        print('Waiting for "Hey ECHO"...')

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.chunk_size,
            callback=self._microphone_callback
        ):
            while self.running:
                try:
                    chunk = self.audio_queue.get(timeout=1)

                except queue.Empty:
                    continue

                if self._check_wake_word(chunk):

                    self._clear_queue()

                    audio = self._record_user_input()

                    self.wake_model.reset()

                    if audio is not None:

                        text = self._transcribe(audio)

                        text = self.clean_input(text)

                        if text:
                            # Next step:
                            # Send text to ECHO Brain / LLM
                            pass

                    time.sleep(self.listening_cooldown)

                    print('Waiting for "Hey ECHO"...')

    def stop(self):
        self.running = False

    # =========================================================
    # MICROPHONE PLUMBING
    # =========================================================

    def _microphone_callback(
        self,
        indata,
        frames,
        time_info,
        status
    ):
        if status:
            print(status)

        self.audio_queue.put(
            indata.copy()
        )

    def _clear_queue(self):

        while not self.audio_queue.empty():

            try:
                self.audio_queue.get_nowait()

            except queue.Empty:
                break

    def _get_audio_level(self, audio):

        audio = audio.astype(
            np.float32
        )

        return float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

    # =========================================================
    # STEP 1: WAKE WORD CHECK
    # =========================================================

    def _check_wake_word(self, chunk):
        
        audio = np.asarray(
            chunk,
            dtype=np.int16
        ).flatten()

        prediction = self.wake_model.predict(
            audio
        )

        if not prediction:
            return False

        score = max(
            float(value)
            for value in prediction.values()
        )

        if score >= self.wake_threshold:

            print(
                f"\nHey ECHO detected ({score:.2f})"
            )

            return True

        return False

    # =========================================================
    # STEP 2: RECORD USER INPUT
    # Stops after:
    # - 1.5 seconds of silence after speech starts
    # OR
    # - 30 seconds maximum recording duration
    # =========================================================

    def _record_user_input(self):

        print("Listening...")

        send_frontend_event("LISTENING_STARTED")

        recorded_audio = []

        silence_start = None

        user_started_speaking = False

        recording_start = time.monotonic()
        try:
            while self.running:

                # Maximum recording safety limit
                if (
                    time.monotonic() - recording_start
                    >= self.max_recording_duration
                ):
                    print(
                        "Maximum recording duration reached."
                    )
                    break

                try:
                    chunk = self.audio_queue.get(
                        timeout=1
                    )

                except queue.Empty:
                    continue

                audio = np.asarray(
                    chunk,
                    dtype=np.int16
                ).flatten()

                recorded_audio.append(
                    audio.copy()
                )

                level = self._get_audio_level(
                    audio
                )

                if level >= self.silence_threshold:

                    user_started_speaking = True

                    silence_start = None

                elif user_started_speaking:

                    if silence_start is None:
                        silence_start = time.monotonic()

                    if (
                        time.monotonic() - silence_start
                        >= self.silence_duration
                    ):
                        print(
                            "User stopped speaking."
                        )

                        break

        finally:
            send_frontend_event("LISTENING_FINISHED")               

        if not recorded_audio:
            return None

        audio = np.concatenate(
            recorded_audio
        )

        audio = (
            audio.astype(np.float32)
            / 32768.0
        )

        duration = (
            len(audio)
            / self.sample_rate
        )

        print(
            f"Audio captured: {duration:.2f} seconds"
        )

        return audio

    # =========================================================
    # STEP 3: SPEECH TO TEXT
    # =========================================================

    def _transcribe(self, audio):

        print(
            "Converting speech to text..."
        )

        try:

            segments, info = (
                self.whisper_model.transcribe(
                    audio,
                    language="en",
                    beam_size=5,
                    vad_filter=False
                )
            )

            return " ".join(
                segment.text.strip()
                for segment in segments
            ).strip()

        except Exception as error:

            print(
                f"Whisper error: {error}"
            )

            return ""

    # =========================================================
    # STEP 4: VALIDATE THE TRANSCRIBED TEXT
    # =========================================================

    def clean_input(self, text):

        if not text:
            print("No speech detected.")
            return None

        text = text.strip()

        if not text:
            print("Empty transcription.")
            return None
        print(text)
        return text
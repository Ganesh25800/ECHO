import time

import cv2

import numpy as np

from insightface.app import FaceAnalysis

from deepface import DeepFace

from core.cental_hub import echo_data


class Camera:

    def __init__(self, echo_data):

        # =====================================================
        # CAMERA SETTINGS
        # =====================================================
        self.echo_data = echo_data
        self.camera_index = 0

        self.dont_add_embeddings = False

        self.capture_interval = 15

        self.camera = None

        self.running = False

        # =====================================================
        # MODELS
        # =====================================================

        self.face_model = None

        # Load InsightFace when Camera object is created
        self.face_model = self._load_face_model()


    # =========================================================
    # LOAD INSIGHTFACE MODEL
    # =========================================================

    def _load_face_model(self):

        print("Loading InsightFace...")

        try:

            model = FaceAnalysis(
                name="buffalo_l",
                providers=[
                    "CPUExecutionProvider"
                ]
            )

            model.prepare(
                ctx_id=0,
                det_size=(640, 640)
            )

            print("InsightFace loaded.")

            return model

        except Exception as error:

            print(
                f"Failed to load InsightFace: {error}"
            )

            raise


    # =========================================================
    # START CAMERA WORKER
    # Called by the camera thread created by Manager
    # =========================================================

    def start(self):

        self.running = True

        print("Starting ECHO camera...")

        self.camera = cv2.VideoCapture(
            self.camera_index
        )

        if not self.camera.isOpened():

            self.running = False

            raise RuntimeError(
                "Unable to open camera."
            )

        print("ECHO camera started.")

        try:

            while self.running:

                # =============================================
                # STEP 1
                # CAPTURE ONE FRAME
                # =============================================

                frame = self.capture()

                if frame is None:

                    print(
                        "Camera frame capture failed."
                    )

                    time.sleep(
                        self.capture_interval
                    )

                    continue

                # =============================================
                # STEP 2
                # DETECT ALL FACES
                # =============================================

                faces = self.detect_faces(
                    frame
                )

                if not faces:

                    print(
                        "No faces detected."
                    )

                    self.final_stage(
                        [],
                        []
                    )

                    time.sleep(
                        self.capture_interval
                    )

                    continue

                # =============================================
                # STEP 3
                # GET ALL EMBEDDINGS
                # =============================================

                embeddings = []

                # =============================================
                # STEP 4
                # GET EMOTION FOR EACH FACE
                # =============================================

                emotions = []

                for face in faces:

                    embedding = (
                        self.convert_to_embedding(
                            face
                        )
                    )

                    if embedding is None:
                        continue

                    face_image = (
                        self.crop_face(
                            frame,
                            face
                        )
                    )

                    emotion = (
                        self.analyze_emotion(
                            face_image
                        )
                    )

                    embeddings.append(
                        embedding
                    )

                    emotions.append(
                        emotion
                    )

                # =============================================
                # STEP 5
                # FINAL CAMERA STAGE
                # =============================================

                self.final_stage(
                    embeddings,
                    emotions
                )

                # =============================================
                # WAIT BEFORE NEXT CAPTURE
                # =============================================

                time.sleep(
                    self.capture_interval
                )

        finally:

            # =============================================
            # ALWAYS RELEASE CAMERA
            # =============================================

            if self.camera is not None:

                self.camera.release()

                self.camera = None

            self.running = False

            print("ECHO camera stopped.")


    # =========================================================
    # CAPTURE ONE FRAME
    # No camera window is displayed.
    # No image is saved.
    # =========================================================

    def capture(self):

        if self.camera is None:

            return None

        success, frame = (
            self.camera.read()
        )

        if not success:

            return None

        return frame


    # =========================================================
    # DETECT ALL FACES
    # =========================================================

    def detect_faces(
        self,
        frame
    ):

        try:

            faces = (
                self.face_model.get(
                    frame
                )
            )

            if not faces:

                return []

            return faces

        except Exception as error:

            print(
                f"InsightFace detection error: {error}"
            )

            return []


    # =========================================================
    # CONVERT ONE FACE INTO EMBEDDING
    # =========================================================

    def convert_to_embedding(
        self,
        face
    ):

        try:

            embedding = (
                face.normed_embedding
            )

            if embedding is None:

                print(
                    "Face embedding could not be generated."
                )

                return None

            return np.asarray(
                embedding,
                dtype=np.float32
            )

        except Exception as error:

            print(
                f"InsightFace embedding error: {error}"
            )

            return None


    # =========================================================
    # CROP ONE FACE FROM FRAME
    # =========================================================

    def crop_face(
        self,
        frame,
        face
    ):

        try:

            x1, y1, x2, y2 = (
                face.bbox.astype(int)
            )

            frame_height, frame_width = (
                frame.shape[:2]
            )

            x1 = max(
                0,
                x1
            )

            y1 = max(
                0,
                y1
            )

            x2 = min(
                frame_width,
                x2
            )

            y2 = min(
                frame_height,
                y2
            )

            if x2 <= x1 or y2 <= y1:

                return None

            face_image = frame[
                y1:y2,
                x1:x2
            ]

            if face_image.size == 0:

                return None

            return face_image

        except Exception as error:

            print(
                f"Face crop error: {error}"
            )

            return None


    # =========================================================
    # ANALYZE FACIAL EMOTION
    # ONE FACE AT A TIME
    # =========================================================

    def analyze_emotion(
        self,
        face_image
    ):

        if face_image is None:

            return None

        try:

            result = DeepFace.analyze(
                img_path=face_image,
                actions=[
                    "emotion"
                ],
                enforce_detection=False,
                silent=True
            )

            # =================================================
            # DeepFace can return either dictionary or list
            # =================================================

            if isinstance(
                result,
                list
            ):

                if not result:

                    return None

                result = result[0]

            if not isinstance(
                result,
                dict
            ):

                return None

            dominant_emotion = (
                result.get(
                    "dominant_emotion"
                )
            )

            emotion_scores = (
                result.get(
                    "emotion",
                    {}
                )
            )

            if dominant_emotion is None:

                return None

            confidence = (
                emotion_scores.get(
                    dominant_emotion,
                    0.0
                )
            )

            return {
                "dominant_emotion":
                    dominant_emotion,

                "confidence":
                    float(confidence),

                "scores":
                    emotion_scores
            }

        except Exception as error:

            print(
                f"DeepFace error: {error}"
            )

            return None


    # =========================================================
    # FINAL STAGE
    #
    # embeddings[0] belongs to emotions[0]
    # embeddings[1] belongs to emotions[1]
    # embeddings[2] belongs to emotions[2]
    # etc.
    # =========================================================

    def final_stage(self,embeddings,emotions):
        
        if not self.dont_add_embeddings:
            self.echo_data.add_camera_data(embeddings,emotions)


    # =========================================================
    # STOP CAMERA WORKER
    # Called by Manager
    # =========================================================

    def stop(self):

        print(
            "Stopping ECHO camera..."
        )

        self.running = False
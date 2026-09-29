from huggingface_hub import snapshot_download, hf_hub_download
from urllib.request import urlretrieve
from pathlib import Path

def download_brain():
    MODEL_REPO = "Qwen/Qwen2.5-7B-Instruct-GGUF"
    MODEL_DIR = Path("./models/qwen2.5-7b-instruct")
    
    snapshot_download(
        repo_id=MODEL_REPO,
        local_dir=MODEL_DIR,
        allow_patterns=["*q4_k_m*.gguf"],
    )

    existing_models = list(MODEL_DIR.glob("*.gguf"))
    
    if existing_models:
        return True
    else:
        return False


def download_kokoro():
    MODEL_DIR = Path("./models/kokoro")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Files
    MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx"
    VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin"

    MODEL_PATH = MODEL_DIR / "kokoro-v1.0.onnx"
    VOICES_PATH = MODEL_DIR / "voices-v1.0.bin"

    try:

        if not MODEL_PATH.exists():
            urlretrieve(MODEL_URL, MODEL_PATH)
        

        if not VOICES_PATH.exists():
            urlretrieve(VOICES_URL, VOICES_PATH)

        return True    

    except:
        return False


def download_classifier():

    MODEL_DIR = Path("./models/classifier")

    REPO_ID = "ggml-org/gemma-3-1b-it-GGUF"
    FILENAME = "gemma-3-1b-it-Q4_K_M.gguf"

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / FILENAME

    if model_path.exists():
        return True

    try:
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODEL_DIR
        )
        return True
    except:
        return False


def download_wake_word_feature_models():

    BASE_DIR = Path(__file__).resolve().parent.parent

    WAKE_WORD_MODEL_DIR = (
        BASE_DIR
        / "models"
        / "wake_word"
    )


    MELSPECTROGRAM_URL = (
        "https://github.com/dscripka/openWakeWord/"
        "releases/download/v0.5.1/melspectrogram.onnx"
    )

    EMBEDDING_MODEL_URL = (
        "https://github.com/dscripka/openWakeWord/"
        "releases/download/v0.5.1/embedding_model.onnx"
    )

    WAKE_WORD_MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    models = {
        "melspectrogram.onnx": MELSPECTROGRAM_URL,
        "embedding_model.onnx": EMBEDDING_MODEL_URL
    }

    for model_name, model_url in models.items():

        model_path = (
            WAKE_WORD_MODEL_DIR
            / model_name
        )

        # Skip model if already downloaded
        if model_path.exists():
            print(
                f"{model_name} already exists."
            )
            continue

        try:

            print(
                f"Downloading {model_name}..."
            )

            urlretrieve(
                model_url,
                model_path
            )

            print(
                f"{model_name} downloaded successfully."
            )

        except Exception as error:

            print(
                f"Failed to download "
                f"{model_name}: {error}"
            )

            # Remove incomplete download
            if model_path.exists():
                model_path.unlink()

            return False

    return True          

    
    

    
import os
import json

# -----------------------------------------------------------------------------
# Module: Google Gemini API Configuration
# -----------------------------------------------------------------------------
# This module handles loading credentials and configuring parameters for
# interacting with the Google Generative Language API (Gemini).
# It reads the API key from a local file and reads model and generation
# settings from environment variables, providing sensible defaults.

# -------- Google Gemini API Key Loading --------
# Path to the file containing the Google API key (one-time setup required).
_API_KEY_PATH = os.path.join(os.path.dirname(__file__), "google_api_key.txt")

try:
    # Open the API key file in UTF-8 encoding to support non-ASCII characters.
    with open(_API_KEY_PATH, "r", encoding="utf-8") as f:
        API_KEY = f.read().strip() # Remove any leading/trailing whitespace
    # Ensure the file was not empty
    if not API_KEY:
        raise ValueError("google_api_key.txt is empty")
except Exception as e:
    # Raise a runtime error to fail fast if the API key cannot be loaded
    raise RuntimeError(f"Failed to load Google API key from {_API_KEY_PATH}: {e}")

# -------- Google Generative Language API Endpoints --------
# Base URL for the Generative Language API; can be overridden by env var.
BASE_URL = os.getenv(
    "GOOGLE_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/models"
)

# Model name for the API requests (e.g., "gemini-1.5-flash"); override via env var.
MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "gemini-1.5-flash")

# -------- Generation Parameters for Gemini --------
# These parameters control the sampling behavior of the language model.
# They can each be overridden by corresponding environment variables.
GOOGLE_GEN_CONFIG = {
    # Controls randomness: higher = more creative, lower = more deterministic.
    "temperature": float(os.getenv("GOOGLE_TEMPERATURE", 0.7)),

    # Nucleus sampling probability: choose from top_p probability mass.
    "top_p": float(os.getenv("GOOGLE_TOP_P", 0.95)),

    # Number of candidate completions to generate per prompt.
    "candidateCount": int(os.getenv("GOOGLE_CANDIDATE_COUNT", 1)),

    # Maximum number of tokens allowed in a single API response.
    "maxOutputTokens": int(os.getenv("GOOGLE_MAX_OUTPUT_TOKENS", 2048)),

    # Sequences at which the model will stop generating further tokens.
    # Expected to be a JSON-formatted list in the environment variable.
    "stopSequences": json.loads(os.getenv("GOOGLE_STOP_SEQUENCES", "[]")),
}


# -----------------------------------------------------------------------------
# Module: Local TinyLLaMA Model Configuration
# -----------------------------------------------------------------------------
# This module defines the configuration parameters for running inference
# against a locally hosted, quantized TinyLLaMA chat model. All settings
# can be overridden via environment variables for flexibility in different
# deployment environments.

# -------- Local Model Path --------
# Absolute filesystem path to the quantized TinyLLaMA model file.
# It is strongly recommended to use an absolute path to avoid ambiguity.
# Override via the LOCAL_MODEL_PATH environment variable if needed.
LOCAL_MODEL_PATH = os.getenv(
    "LOCAL_MODEL_PATH",
    "/home/cheng/Desktop/tinyllama1b/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
)

# -------- Local Generation Parameters --------
# Hyperparameters controlling the sampling behavior of the local model.
# Each parameter may be overridden by the corresponding environment variable.
# Values are cast to the appropriate type and validated at load time.
LOCAL_GEN_CONFIG = {
    # Controls randomness of token sampling: higher temperature → more diverse output.
    "temperature": float(os.getenv("LOCAL_TEMPERATURE", 0.7)),

    # Nucleus sampling: restricts token selection to the top_p probability mass.
    "top_p": float(os.getenv("LOCAL_TOP_P", 0.95)),

    # Limits token pool to the top_k highest-probability tokens at each step.
    "top_k": int(os.getenv("LOCAL_TOP_K", 40)),

    # Maximum number of tokens the model is allowed to generate in one response.
    "max_tokens": int(os.getenv("LOCAL_MAX_OUTPUT_TOKENS", 2048)),
    
    # List of token sequences where generation will stop.
    # Default stop tokens signify speaker changes in a chat transcript.
    "stop": json.loads(os.getenv("LOCAL_STOP_TOKENS", '["User:","Assistant:"]')),
}

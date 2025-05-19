from llama_cpp import Llama
import os

# -----------------------------------------------------------------------------
# Global Configuration
# -----------------------------------------------------------------------------
# Holds all configurable parameters for the TinyLLaMA model and system prompt.
# Paths are resolved to absolute to avoid working-directory issues.
CONFIG = {
    # Filesystem path to the quantized TinyLLaMA model file
    "MODEL_PATH": os.path.abspath(
        "/home/azureuser/tinyllama1b/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    ),
    # Path to the system prompt text that primes the assistant's behavior
    "SYSTEM_PROMPT_PATH": os.path.abspath("./system_prompt.txt"),
    # Context window size for the model (number of tokens of memory)
    "N_CTX": 2048,
    # Number of CPU threads to use for model inference
    "N_THREADS": 6,
    # Maximum number of tokens the model is allowed to generate
    "MAX_TOKENS": 512,
    # Sampling temperature: higher = more creative, lower = more deterministic
    "TEMPERATURE": 0.7
}

# -----------------------------------------------------------------------------
# Model Initialization
# -----------------------------------------------------------------------------
def init_model() -> Llama:
    """
    Instantiate and return a Llama model instance using the global CONFIG settings.

    Uses:
        - MODEL_PATH for loading the quantized model file.
        - N_CTX to set the model's context window.
        - N_THREADS to configure parallelism for inference.

    Returns:
        A configured Llama object ready for chat completions.
    """
    llm = Llama(
        model_path=CONFIG["MODEL_PATH"],
        n_ctx=CONFIG["N_CTX"],
        n_threads=CONFIG["N_THREADS"]
    )
    return llm

# -----------------------------------------------------------------------------
# System Prompt Loader
# -----------------------------------------------------------------------------
def get_default_system_prompt() -> str:
    """
    Read and return the system prompt from disk.

    The system prompt is used to define the assistant's persona,
    style guidelines, and any initial instructions for all chat sessions.

    Returns:
        The full text of the system prompt.
    """
    with open(CONFIG["SYSTEM_PROMPT_PATH"], "r", encoding="utf-8") as f:
        return f.read().strip()

# -----------------------------------------------------------------------------
# Streaming Chat Response Generator
# -----------------------------------------------------------------------------
def chat_stream(llm: Llama, messages: list[dict]) -> str:
    """
    Stream chat completion tokens from the TinyLLaMA model.

    Args:
        llm: Initialized Llama model instance.
        messages: List of message dicts (with 'role' and 'content')
                  representing the conversation history plus the latest user prompt.

    Yields:
        Individual text fragments as the model generates them in real time.
    """
    # Begin a streaming chat completion request
    stream = llm.create_chat_completion(
        messages=messages,
        stream=True,
        max_tokens=CONFIG["MAX_TOKENS"],
        temperature=CONFIG["TEMPERATURE"]
    )
    # Iterate over each incremental chunk returned
    for chunk in stream:
        # Extract any new content from the 'delta' field of the first choice
        content = chunk["choices"][0]["delta"].get("content")
        if content:
            # Yield only non-empty text fragments
            yield content

# -----------------------------------------------------------------------------
# One-Shot Chat Completion
# -----------------------------------------------------------------------------
def chat_once(llm: Llama, messages: list[dict]) -> str:
    """
    Perform a single-turn chat completion with the TinyLLaMA model.

    Args:
        llm: Initialized Llama model instance.
        messages: List of message dicts (with 'role' and 'content')
                  representing the conversation history plus the latest user prompt.

    Returns:
        The complete assistant response as a single concatenated string.
    """
    # Request a full, non-streaming chat completion
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=CONFIG["MAX_TOKENS"],
        temperature=CONFIG["TEMPERATURE"]
    )
    # Extract and return the generated content from the first choice
    return response["choices"][0]["message"]["content"]

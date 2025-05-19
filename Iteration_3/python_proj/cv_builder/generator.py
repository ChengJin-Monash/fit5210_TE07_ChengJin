import os
import time  # For optional benchmarking and timing operations
import re
from llama_cpp import Llama
from prompt_builder import (
    build_profile_prompt,
    build_education_prompt,
    build_work_prompt
)

# === Model Configuration ===
# Path to the local GGUF-formatted TinyLLaMA model file
model_path = os.path.expanduser(
    "/home/azureuser/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
)

# Inference parameters for the LLaMA model
n_ctx = 2048           # Maximum context window size (number of tokens)
temperature = 0.0      # Sampling temperature: 0.0 for deterministic output
top_k = 5              # Number of highest-probability tokens to keep for sampling
repeat_penalty = 1.1    # Penalty factor to discourage repeated text sequences

# Instantiate the LLaMA model with the specified configuration
llm = Llama(
    model_path=model_path,
    n_ctx=n_ctx,
    verbose=False       # Suppress verbose logging during inference
)

# === Utility Functions ===

def clean_text(text: str) -> str:
    """
    Normalize generated text by:
      1. Splitting into paragraphs on blank lines.
      2. Merging any line breaks within each paragraph into spaces.
      3. Reassembling into a single string with paragraphs separated by newlines.

    Args:
        text: Raw multi-line string output from the model.
    Returns:
        A cleaned string where each paragraph is on one line.
    """
    # Remove leading/trailing whitespace and split on double newlines
    paragraphs = text.strip().split("\n\n")
    cleaned_paragraphs = []
    for p in paragraphs:
        # Collapse all line breaks in paragraph into a single space
        single_line = re.sub(r"\s*\n\s*", " ", p.strip())
        cleaned_paragraphs.append(single_line)
    # Rejoin paragraphs with a blank line between them
    return "\n".join(cleaned_paragraphs)


def trim_to_last_period(text: str) -> str:
    """
    Truncate the input text at the last complete sentence boundary.

    Args:
        text: A string which may end mid-sentence.
    Returns:
        A substring ending at the last period (".").
        If no period is found, returns the original text.
    """
    text = text.strip()
    # If text already ends with a period, return as-is
    if text.endswith("."):
        return text
    # Find the index of the last period
    last_idx = text.rfind(".")
    # Include the period in the returned text if found
    return text[:last_idx + 1] if last_idx != -1 else text


def clean_education_output(text: str) -> str:
    """
    Post-process text specific to the Education section:
      1. Clean line breaks and paragraph formatting.
      2. Trim output to the last full sentence before any separators.

    Args:
        text: Raw model output intended for the Education section.
    Returns:
        A cleaned, sentence-complete string without trailing separators.
    """
    cleaned = clean_text(text)
    # Split off any trailing separator blocks and trim
    main_content = cleaned.split("------")[0]
    return trim_to_last_period(main_content)

# === CV Generation (Full Output) ===

def generate_cv_text(user_info: dict) -> dict:
    """
    Generate a complete CV based on structured user input.

    This function orchestrates the following steps:
      1. Initialize log storage and helper function.
      2. Estimate token budgets for each CV section based on data counts.
      3. Build tailored prompts for Profile, Education, and Work sections.
      4. Run the LLaMA model for each prompt and clean its output.
      5. Compose human-editable headings and bullet summaries.
      6. Assemble final text, save to file, and return structured output.

    Args:
        user_info (dict): A dictionary containing user details:
            - 'name': Candidate's full name.
            - 'education': List of education record dicts.
            - 'work_experience': List of work experience dicts.
            - 'job' (optional): Dict with 'title' and 'company_name'.

    Returns:
        dict: Contains generated CV headings, content per section, lists, and logs.
    """
    # --- 1. Initialize logging ---
    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    # --- 2. Estimate token budgets ---
    edu_len = len(user_info.get("education", []))
    work_len = len(user_info.get("work_experience", []))
    total_len = edu_len + work_len

    # Allocate tokens: profile approx half entries * 60, others based on count
    max_tokens_profile = int(((total_len / 2) + 0.5) * 60)
    max_tokens_edu = int((edu_len + 0.5) * 60) if edu_len > 0 else 0
    max_tokens_work = int((work_len + 0.5) * 60)

    # --- 3. Build prompts ---
    profile_prompt = build_profile_prompt(user_info)
    edu_prompt = build_education_prompt(user_info) if edu_len > 0 else None
    work_prompt = build_work_prompt(user_info)

    # --- 4. LLaMA inference helper ---
    def run_llama(prompt_text, label="", max_tokens=200):
        """
        Send prompt to LLaMA, log timing, and clean output.

        Args:
            prompt_text (str): The text to feed the model.
            label (str): Section name for logging.
            max_tokens (int): Token limit for generation.

        Returns:
            str: Cleaned, complete-sentence output.
        """
        log(f"🤖 Generating {label}...")
        start = time.time()
        output = llm(
            prompt=prompt_text,
            max_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            repeat_penalty=repeat_penalty
        )
        duration = time.time() - start
        log(f"✅ {label} done in {duration:.2f}s")
        return trim_to_last_period(clean_text(output["choices"][0]["text"]))

    # Generate content for each CV section
    profile_output = run_llama(profile_prompt, "Profile", max_tokens_profile)
    education_output = run_llama(edu_prompt, "Education", max_tokens_edu) if edu_prompt else ""
    work_output = run_llama(work_prompt, "Experience", max_tokens_work)

    # --- 5. Prepare headings and summaries ---
    # Top-of-document heading with placeholders for user input
    cv_heading = f"Name: {user_info.get('name', '[Unknown]')}\n" \
                 f"Phone: [Please enter your phone number]\n" \
                 f"E-mail: [Please enter your email address]"

    profile_heading = "Profile:\n[You can briefly add a few sentences to describe yourself. Example:]"

    # Bullet-style lists of raw entries for manual editing
    education_list = [
        f"{edu.get('degree_type', '')} of {edu.get('degree_name', '')} at {edu.get('institution', '')} ({edu.get('year_start', '')} - {edu.get('year_end', '')})"
        for edu in user_info.get("education", [])
    ]

    experience_list = [
        f"{w.get('job_title', '')} at {w.get('organization', '')} ({w.get('year_start', '')} - {w.get('year_end', '')})"
        for w in user_info.get("work_experience", [])
    ]

    education_heading = (
        "Education:\n[You can briefly describe your education experience. Example:]"
        if education_list else
        "Education:\n[You can fill in your education background here.]"
    )

    experience_heading = "Work Experience:\n[You can briefly describe your experience. Example:]"

    # --- 6. Assemble final document and persist ---
    lines = [cv_heading + "\n", profile_heading, profile_output + "\n"]
    lines.append(education_heading)
    if education_list:
        lines.extend(education_list)
        lines.append(education_output + "\n")
    else:
        lines.append("[You can fill in your education background here.]\n")

    lines.append(experience_heading.split("\n")[0])
    lines.extend(experience_list)
    lines.append(work_output + "\n")

    final_text = "\n".join(lines)

    # Save generated CV to a file
    with open("cv_output.txt", "w", encoding="utf-8") as f:
        f.write(final_text)
    log("✅ CV saved to cv_output.txt")

    # Return a structured representation for API or further processing
    return {
        "cv_heading": cv_heading,
        "profile_heading": profile_heading,
        "profile_content": profile_output,
        "education_heading": education_heading,
        "education_list": education_list,
        "education_content": education_output if education_list else "",
        "experience_heading": experience_heading,
        "experience_list": experience_list,
        "experience_content": work_output,
        "logs": logs
    }

# === CV Generation (Streaming Version) ===
def generate_cv_stream(user_info: dict):
    """
    Stream CV content in real-time using Server-Sent Events (SSE).

    This generator yields:
      - Initial heading placeholders.
      - Section-by-section log messages and content lines.
      - A final completion event.

    Args:
        user_info (dict): Same structure as for generate_cv_text.

    Yields:
        str: Formatted SSE "data:" frames with '\n\n' separators.
    """
    # Local import for timing inside generator
    import time

    # Helper to yield log messages as SSE events
    def stream_log(msg):
        print(msg)
        yield f"data: {msg}\n\n"

    start_all = time.time()

    # Estimate token budgets (same logic as synchronous version)
    edu_len = len(user_info.get("education", []))
    work_len = len(user_info.get("work_experience", []))
    total_len = edu_len + work_len

    max_tokens_profile = int(((total_len / 2) + 0.5) * 60)
    max_tokens_edu = int((edu_len + 0.5) * 60) if edu_len > 0 else 0
    max_tokens_work = int((work_len + 0.5) * 60)

    # Prepare prompts
    profile_prompt = build_profile_prompt(user_info)
    edu_prompt = build_education_prompt(user_info) if edu_len > 0 else None
    work_prompt = build_work_prompt(user_info)

    # --- CV heading events ---
    name = user_info.get("name", "[Unknown]")
    yield f"data: Name: {name}\n\n"
    yield "data: Phone: [Please enter your phone number]\n\n"
    yield "data: E-mail: [Please enter your email address]\n\n"

    # --- Profile section ---
    yield from stream_log("Generating Profile...")
    profile_heading = "Profile:\n[You can briefly add a few sentences to describe yourself. Example:]"
    yield f"data: {profile_heading}\n\n"
    start = time.time()
    profile_output = llm(
        prompt=profile_prompt,
        max_tokens=max_tokens_profile,
        temperature=temperature,
        top_k=top_k,
        repeat_penalty=repeat_penalty
    )
    profile_text = trim_to_last_period(clean_text(profile_output["choices"][0]["text"]))
    for line in profile_text.split("\n"):
        yield f"data: {line.strip()}\n\n"
    duration = time.time() - start
    yield f"data: ✅ Profile done in {duration:.2f}s\n\n"

    # --- Education section ---
    if edu_prompt:
        yield from stream_log("Generating education parts...")
        education_heading = (
            "Education:\n[You can briefly describe your education experience. Example:]"
            if edu_len else
            "Education:\n[You can fill in your education background here.]"
        )
        yield f"data: {education_heading}\n\n"
        start = time.time()
        edu_output = llm(
            prompt=edu_prompt,
            max_tokens=max_tokens_edu,
            temperature=temperature,
            top_k=top_k,
            repeat_penalty=repeat_penalty
        )
        edu_text = trim_to_last_period(clean_text(edu_output["choices"][0]["text"]))
        for line in edu_text.split("\n"):
            yield f"data: {line.strip()}\n\n"
        duration = time.time() - start
        yield f"data: ✅ Education done in {duration:.2f}s\n\n"

    # --- Work Experience section ---
    yield from stream_log("Generating work experience parts...")
    experience_heading = "Work Experience:\n[You can briefly describe your experience. Example:]"
    yield f"data: {experience_heading}\n\n"
    start = time.time()
    work_output = llm(
        prompt=work_prompt,
        max_tokens=max_tokens_work,
        temperature=temperature,
        top_k=top_k,
        repeat_penalty=repeat_penalty
    )
    work_text = trim_to_last_period(clean_text(work_output["choices"][0]["text"]))
    for line in work_text.split("\n"):
        yield f"data: {line.strip()}\n\n"
    duration = time.time() - start
    yield f"data: ✅ Work Experience done in {duration:.2f}s\n\n"

    # --- Completion event ---
    total_duration = time.time() - start_all
    yield f"data: ✅ CV generated in {total_duration:.2f}s\n\n"
    yield "data: [DONE]\n\n"


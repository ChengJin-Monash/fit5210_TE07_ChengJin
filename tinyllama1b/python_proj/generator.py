# === generator.py ===

import os
import time
import re
from llama_cpp import Llama
from prompt_builder import (
    build_profile_prompt,
    build_education_prompt,
    build_work_prompt
)

# === Model Configuration ===

# Set the path to the local GGUF format language model
model_path = os.path.expanduser(
    "/home/azureuser/tinyllama1b/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
)

# LLM inference configuration parameters
n_ctx = 2048
temperature = 0.0
top_k = 20
repeat_penalty = 1.1

# Initialize the LLaMA model instance
llm = Llama(
    model_path=model_path,
    n_ctx=n_ctx,
    verbose=False
)

# === Utility Functions ===

def clean_text(text: str) -> str:
    """
    Clean the generated text by merging lines within a paragraph
    and preserving paragraph separation.
    """
    paragraphs = text.strip().split("\n\n")
    cleaned = [re.sub(r"\s*\n\s*", " ", p.strip()) for p in paragraphs]
    return "\n".join(cleaned)

def trim_to_last_period(text: str) -> str:
    """
    Trims the text up to the last full stop to avoid incomplete sentences.
    """
    text = text.strip()
    if text.endswith("."):
        return text
    last_period = text.rfind(".")
    return text[:last_period + 1] if last_period != -1 else text

def clean_education_output(text: str) -> str:
    """
    Process education-related output to remove extra sections
    and ensure it ends at the last full stop.
    """
    text = clean_text(text)
    return trim_to_last_period(text.split("------")[0])

# === CV Generation (Full Output) ===

def generate_cv_text(user_info: dict) -> dict:
    """
    Generate a complete CV based on structured user input.
    The result includes headings, content, and metadata for each section.
    """

    logs = []

    def log(msg):
        print(msg)
        logs.append(msg)

    # Count the number of entries for estimation
    edu_len = len(user_info.get("education", []))
    work_len = len(user_info.get("work_experience", []))
    total_len = edu_len + work_len

    # Dynamically allocate token limits based on content size
    max_tokens_profile = int(((total_len / 2) + 0.5) * 60)
    max_tokens_edu = int((edu_len + 0.5) * 60) if edu_len > 0 else 0
    max_tokens_work = int((work_len + 0.5) * 60)

    # Build prompts for each section
    profile_prompt = build_profile_prompt(user_info)
    edu_prompt = build_education_prompt(user_info) if edu_len > 0 else None
    work_prompt = build_work_prompt(user_info)

    def run_llama(prompt_text, label="", max_tokens=200):
        """
        Run LLaMA model on a given prompt and log performance.
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

    # Generate each section of the CV
    profile_output = run_llama(profile_prompt, "Profile", max_tokens_profile)
    education_output = run_llama(edu_prompt, "Education", max_tokens_edu) if edu_prompt else ""
    work_output = run_llama(work_prompt, "Experience", max_tokens_work)

    # Prepare human-editable sections
    cv_heading = f"Name: {user_info.get('name', '[Unknown]')}\n" \
                 f"Phone: [Please enter your phone number]\n" \
                 f"E-mail: [Please enter your email address]"

    profile_heading = "Profile:\n[You can briefly add a few sentences to describe yourself. Example:]"

    # Create summary lines for education and experience
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

    # Assemble CV text lines
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

    # Return result as dictionary
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
    import time

    def stream_log(msg):
        print(msg)
        yield f"data: {msg}\n\n"

    start_all = time.time()

    edu_len = len(user_info.get("education", []))
    work_len = len(user_info.get("work_experience", []))
    total_len = edu_len + work_len

    max_tokens_profile = int(((total_len / 2) + 0.5) * 60)
    max_tokens_edu = int((edu_len + 0.5) * 60) if edu_len > 0 else 0
    max_tokens_work = int((work_len + 0.5) * 60)

    profile_prompt = build_profile_prompt(user_info)
    edu_prompt = build_education_prompt(user_info) if edu_len > 0 else None
    work_prompt = build_work_prompt(user_info)

    # === CV heading ===
    name = user_info.get("name", "[Unknown]")
    yield f"data: Name: {name}\n\n"
    yield "data: Phone: [Please enter your phone number]\n\n"
    yield "data: E-mail: [Please enter your email address]\n\n"

    # === Profile Section ===
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

    # === Education Section ===
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

    # === Work Section ===
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

    # === Final log ===
    total_duration = time.time() - start_all
    yield f"data: ✅ CV generated in {total_duration:.2f}s\n\n"
    yield "data: [DONE]\n\n"

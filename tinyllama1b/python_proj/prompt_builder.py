def build_profile_prompt(user_info: dict) -> str:
    """
    Build a prompt for generating a short self-description based on user's name,
    education, and work history. This is used to generate the 'Profile' section
    of the CV in first-person perspective.

    Args:
        user_info (dict): Dictionary containing user's basic information,
                          education, and work experience.

    Returns:
        str: The formatted prompt to feed into the LLM for profile generation.
    """
    name = user_info.get("name", "Unknown")

    # Format education entries as lines
    edu_lines = []
    for edu in user_info.get("education", []):
        edu_line = f"{edu.get('degree_type', '')} of {edu.get('degree_name', '')} at {edu.get('institution', '')} ({edu.get('year_start', '')} - {edu.get('year_end', '')})"
        edu_lines.append(edu_line)
    edu_text = "\n".join(edu_lines) if edu_lines else "[No education info]"

    # Format work experience entries as lines
    work_lines = []
    for work in user_info.get("work_experience", []):
        work_line = f"{work.get('job_title', '')} at {work.get('organization', '')} ({work.get('year_start', '')} - {work.get('year_end', '')})"
        work_lines.append(work_line)
    work_text = "\n".join(work_lines) if work_lines else "[No work experience]"

    # Construct the full prompt for the LLM
    prompt = f"""Please one short paragraph (maximum 3 sentences) for the following CV clip, use the first-person perspective.
Don't describe anything other than general profile.
Don't describe anything other than general profile.
Don't describe anything other than general profile.
------
Name: {name}
{edu_text}
{work_text}
Description: Please add Description on personal profile in maximum 1 paragraph.
------
Output as Description:"""

    return prompt


def build_education_prompt(user_info: dict) -> str:
    """
    Build a prompt for generating a short paragraph describing the user's
    education history in first-person perspective.

    Args:
        user_info (dict): Dictionary containing the user's education entries.

    Returns:
        str: The formatted education prompt or an empty string if no education info.
    """
    education = user_info.get("education", [])
    if not education:
        return ""

    edu_lines = []
    for edu in education:
        line = f"Education: {edu.get('degree_type', '')} of {edu.get('degree_name', '')} at {edu.get('institution', '')} ({edu.get('year_start', '')} - {edu.get('year_end', '')})"
        edu_lines.append(line)
    edu_text = "\n".join(edu_lines)

    prompt = f"""Please one short paragraph (maximum 3 sentences) for the following CV clip, use the first-person perspective.
Don't describe anything other than education parts.
Don't describe anything other than education parts.
Don't describe anything other than education parts.
------
{edu_text}
Description: Please add Description on education history in maximum 1 paragraph.
------
Output as Description:"""

    return prompt


def build_work_prompt(user_info: dict) -> str:
    """
    Build a prompt for generating a short paragraph describing the user's
    work experience in first-person perspective.

    Args:
        user_info (dict): Dictionary containing the user's work experience entries.

    Returns:
        str: The formatted work experience prompt or an empty string if none.
    """
    work = user_info.get("work_experience", [])
    if not work:
        return ""

    work_lines = []
    for w in work:
        line = f"Experience: {w.get('job_title', '')} at {w.get('organization', '')} ({w.get('year_start', '')} - {w.get('year_end', '')})"
        work_lines.append(line)
    work_text = "\n".join(work_lines)

    prompt = f"""Please one short paragraph (maximum 3 sentences) for the following CV clip, use the first-person perspective.
Don't describe anything other than work experience.
Don't describe anything other than work experience.
Don't describe anything other than work experience.
------
{work_text}
Description: Please add Description on work experience in maximum 1 paragraph.
------
Output as Description:"""

    return prompt

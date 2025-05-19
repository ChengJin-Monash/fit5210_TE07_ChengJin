def build_profile_prompt(user_info: dict) -> str:
    name = user_info.get("name", "Unknown")

    # Edu
    edu_lines = []
    for edu in user_info.get("education", []):
        edu_line = f"{edu.get('degree_type', '')} of {edu.get('degree_name', '')} at {edu.get('institution', '')} ({edu.get('year_start', '')} - {edu.get('year_end', '')})"
        edu_lines.append(edu_line)
    edu_text = "\n".join(edu_lines) if edu_lines else "[No education info]"

    # Work
    work_lines = []
    for work in user_info.get("work_experience", []):
        work_line = f"{work.get('job_title', '')} at {work.get('organization', '')} ({work.get('year_start', '')} - {work.get('year_end', '')})"
        work_lines.append(work_line)
    work_text = "\n".join(work_lines) if work_lines else "[No work experience]"

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
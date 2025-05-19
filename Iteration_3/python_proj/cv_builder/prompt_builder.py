from typing import Dict, List

def build_profile_prompt(user_info: Dict) -> str:
    """
    Create a prompt for generating the profile section of a CV.
    If a specific job title is provided, tailor the prompt to that position.
    """
    # Extract the user's name or use a default placeholder
    name = user_info.get("name", "Unknown")

    # Compile education summary lines
    edu_lines: List[str] = [
        f"{edu.get('degree_type', '')} of {edu.get('degree_name', '')} at {edu.get('institution', '')} "
        f"({edu.get('year_start', '')}-{edu.get('year_end', '')})"
        for edu in user_info.get('education', [])
    ]

    # Compile work experience summary lines
    work_lines: List[str] = [
        f"{w.get('job_title', '')} at {w.get('organization', '')} "
        f"({w.get('year_start', '')}-{w.get('year_end', '')})"
        for w in user_info.get('work_experience', [])
    ]
    edu_text = "\n".join(edu_lines)
    work_text = "\n".join(work_lines)

    # Retrieve job context if available
    job = user_info.get('job') or {}
    job_title = job.get('title')
    company_name = job.get('company_name')

    # Select the appropriate prompt template
    if job_title:
        prompt = f"""Please write a concise, professional paragraph in the first-person perspective that highlights my key qualifications, skills and achievements relevant to the position "{job_title}" at "{company_name}".
Focus only on information appearing in the CV clip below; do not invent new experiences or details. Use strong action verbs and precise language. In English only.  
------
Name: {name}
{edu_text}
{work_text}
Description: Please add Description on personal profile in maximum 1 paragraph.
------
Output as Description:"""
    else:
        prompt = f"""Please write a concise, professional paragraph in the first-person perspective that highlights my key qualifications, skills and achievements. Focus only on information appearing in the CV clip below; do not invent new experiences or details. Use strong action verbs and precise language. In English only.
------
Name: {name}
{edu_text}
{work_text}
Description: Please add Description on personal profile in maximum 1 paragraph.
------
Output as Description:"""

    return prompt


def build_education_prompt(user_info: Dict) -> str:
    """
    Create a prompt for the education section of a CV.
    Adjust the prompt based on an optional job context.
    """
    # Compile education summary lines
    edu_lines: List[str] = [
        f"{edu.get('degree_type', '')} of {edu.get('degree_name', '')} at {edu.get('institution', '')} "
        f"({edu.get('year_start', '')}-{edu.get('year_end', '')})"
        for edu in user_info.get('education', [])
    ]
    edu_text = "\n".join(edu_lines)

    # Retrieve job context if available
    job = user_info.get('job') or {}
    job_title = job.get('title')
    company_name = job.get('company_name')

    # Select prompt template
    if job_title:
        prompt = f"""Add one very short paragraph for the following CV clip in Education part, use the first-person perspective.
The cv is specific for job: \"{job_title}\" at \"{company_name}\".
Don't describe anything other than education parts.
Don't make up any experiences.
In English only.
------
{edu_text}
Description: Please add Description on education history in maximum 1 paragraph.
------
Output as Description:"""
    else:
        prompt = f"""Add one very short paragraph for the following CV clip in Education part, use the first-person perspective.
Don't describe anything other than education parts.
Don't make up any experiences.
In English only.
------
{edu_text}
Description: Please add Description on education history in maximum 1 paragraph.
------
Output as Description:"""

    return prompt


def build_work_prompt(user_info: Dict) -> str:
    """
    Create a prompt for the work experience section of a CV.
    Adjust the prompt based on an optional job context.
    """
    # Compile work experience summary lines
    work_lines: List[str] = [
        f"{w.get('job_title', '')} at {w.get('organization', '')} "
        f"({w.get('year_start', '')}-{w.get('year_end', '')})"
        for w in user_info.get('work_experience', [])
    ]
    work_text = "\n".join(work_lines)

    # Retrieve job context if available
    job = user_info.get('job') or {}
    job_title = job.get('title')
    company_name = job.get('company_name')

    # Select prompt template
    if job_title:
        prompt = f"""Add one very short paragraph for the following CV clip in Work Experience part, use the first-person perspective.
The cv is specific for job: \"{job_title}\" at \"{company_name}\".
Don't describe anything other than work experience parts.
Don't make up any experiences.
In English only.
------
{work_text}
Description: Please add Description on work experience in maximum 1 paragraph.
------
Output as Description:"""
    else:
        prompt = f"""Add one very short paragraph for the following CV clip in Work Experience part, use the first-person perspective.
Don't describe anything other than work experience parts.
Don't make up any experiences.
In English only.
------
{work_text}
Description: Please add Description on work experience in maximum 1 paragraph.
------
Output as Description:"""

    return prompt


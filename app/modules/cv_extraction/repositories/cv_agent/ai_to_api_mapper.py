from typing import Optional, List
from datetime import date, datetime
from app.modules.cv_extraction.repositories.cv_agent.agent_schema import CVAnalysisResult
from app.modules.cv_extraction.schemas.cv import CVBase, EducationEntry, ExperienceEntry, ProjectEntry, CertificationEntry

# Helper functions
def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.date()
        except Exception:
            continue
    return None

def extract_year(date_str: Optional[str]) -> Optional[int]:
    d = parse_date(date_str)
    return d.year if d else None

def ai_to_cvbase(ai_result: CVAnalysisResult) -> CVBase:
    pi = ai_result.personal_information
    return CVBase(
        name=pi.full_name if pi and pi.full_name else "",
        email=pi.email if pi and pi.email else "",
        phone=pi.phone_number if pi and pi.phone_number else None,
        summary=ai_result.cv_summary,
        education=[
            EducationEntry(
                degree=e.degree_name or "",
                institution=e.institution_name or "",
                start_year=extract_year(e.graduation_date),
                end_year=extract_year(e.graduation_date),
                description=e.description
            ) for e in (ai_result.education_history.items if ai_result.education_history and ai_result.education_history.items else [])
        ],
        experience=[
            ExperienceEntry(
                title=w.job_title or "",
                company=w.company_name or "",
                start_date=parse_date(w.start_date),
                end_date=parse_date(w.end_date),
                description='; '.join(w.responsibilities_achievements) if w.responsibilities_achievements else None
            ) for w in (ai_result.work_experience_history.items if ai_result.work_experience_history and ai_result.work_experience_history.items else [])
        ],
        skills=[s.skill_name for s in (ai_result.skills_summary.items if ai_result.skills_summary and ai_result.skills_summary.items else [])],
        projects=[
            ProjectEntry(
                title=p.project_name or "",
                tech_stack=p.technologies_used or [],
                description=p.description
            ) for p in (ai_result.projects_showcase.items if ai_result.projects_showcase and ai_result.projects_showcase.items else [])
        ] if ai_result.projects_showcase else None,
        certifications=[
            CertificationEntry(
                name=c.certificate_name or "",
                issuer=c.issuing_organization,
                time_period=parse_date(c.issue_date),
                description=None
            ) for c in (ai_result.certificates_and_courses.items if ai_result.certificates_and_courses and ai_result.certificates_and_courses.items else [])
        ] if ai_result.certificates_and_courses else None,
    ) 
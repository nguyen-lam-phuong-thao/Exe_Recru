from app.core.config import GOOGLE_API_KEY
from .cv_processor import CVProcessorWorkflow
from app.modules.cv_extraction.repositories.cv_agent.agent_schema import CVAnalysisResult
import logging
from typing import Optional

class CVAnalyzer:
    """
    Provides a stable interface for analyzing CV content using CVProcessorWorkflow.
    Returns a CVAnalysisResult on success, or None on error.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cv_processor = CVProcessorWorkflow(api_key=GOOGLE_API_KEY)

    async def analyze_cv_content(self, cv_content: str, job_description: Optional[str] = None) -> Optional[CVAnalysisResult]:
        """
        Analyze the given CV content and return a CVAnalysisResult.
        Returns None if an error occurs.
        """
        try:
            self.logger.info(f'Starting CV analysis with content length: {len(cv_content or "")}')
            result = await self.cv_processor.analyze_cv(cv_content, job_description)
            if isinstance(result, CVAnalysisResult):
                return result
            else:
                self.logger.error(f'CV analysis did not return a CVAnalysisResult. Got: {type(result)}')
                return None
        except Exception as e:
            self.logger.exception(f'Error in CVAnalyzer.analyze_cv_content: {str(e)}')
            return None

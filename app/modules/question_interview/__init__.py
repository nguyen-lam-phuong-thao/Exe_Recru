"""
Question Composer Module.
This module provides intelligent question generation for user profiling using LangChain and LangGraph.
"""

import logging

logger = logging.getLogger(__name__)


# Color codes for logging
class LogColors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'


logger.info(f'{LogColors.HEADER}[QuestionComposer-Module] Question Composer module initialized{LogColors.ENDC}')

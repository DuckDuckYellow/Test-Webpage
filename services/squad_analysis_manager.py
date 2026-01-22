"""
Squad Analysis Manager - Orchestrates the analysis workflow.
"""

import os
import uuid
import tempfile
from typing import Tuple, List, Optional, Dict
from flask import session, current_app
from services.parser_factory import ParserFactory
from services.squad_audit_service import SquadAuditService
from services.player_evaluator_service import PlayerEvaluatorService
from models.squad_audit import Squad, SquadAnalysisResult

class SquadAnalysisManager:
    """Manages the end-to-end squad analysis process."""

    def __init__(self):
        self.parser_factory = ParserFactory()
        self.audit_service = SquadAuditService()
        self.player_evaluator = PlayerEvaluatorService()

    def process_squad_upload(self, file_content: str) -> Tuple[Optional[SquadAnalysisResult], List[str]]:
        """
        Processes a squad HTML upload.
        1. Detects parser
        2. Parses squad
        3. Evaluates players
        4. Analyzes squad
        5. Persists to session-linked temporary storage
        """
        errors = []
        try:
            # Detect and get parser
            parser = self.parser_factory.get_parser(file_content)
            
            # Parse HTML
            squad = parser.parse_html(file_content)
            
            # Evaluate roles for all players
            for player in squad.players:
                self.player_evaluator.evaluate_roles(player)
            
            # Analyze squad
            analysis_result = self.audit_service.analyze_squad(squad)
            
            # Persist to safe temporary storage
            self._persist_to_session(file_content)
            
            return analysis_result, errors
            
        except ValueError as ve:
            errors.append(f"Invalid format: {str(ve)}")
            return None, errors
        except Exception as e:
            current_app.logger.error(f"Analysis error: {e}")
            errors.append(f"Processing error: {str(e)}")
            return None, errors

    def get_analysis_from_session(self) -> Optional[SquadAnalysisResult]:
        """
        Retrieves and re-analyzes squad from session-stored HTML.
        """
        html_content = self._get_from_session()
        if not html_content:
            return None
            
        # Re-parse and analyze (stateless but consistent)
        parser = self.parser_factory.get_parser(html_content)
        squad = parser.parse_html(html_content)
        
        for player in squad.players:
            self.player_evaluator.evaluate_roles(player)
            
        return self.audit_service.analyze_squad(squad)

    def _persist_to_session(self, content: str):
        """Stores content in a UUID-named file and saves UUID in session."""
        analysis_id = str(uuid.uuid4())
        
        # Ensure temp directory exists
        temp_dir = os.path.join(tempfile.gettempdir(), 'squad_audit_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, f"{analysis_id}.html")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        session['squad_analysis_id'] = analysis_id
        session.permanent = True

    def _get_from_session(self) -> Optional[str]:
        """Reads content from file linked by session UUID."""
        analysis_id = session.get('squad_analysis_id')
        if not analysis_id:
            return None
            
        temp_dir = os.path.join(tempfile.gettempdir(), 'squad_audit_uploads')
        file_path = os.path.join(temp_dir, f"{analysis_id}.html")
        
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def get_formation_suggestions(self, result: SquadAnalysisResult) -> List[Dict]:
        """Wrapper for formation suggestions."""
        return self.audit_service.suggest_formations(result, top_n=3)

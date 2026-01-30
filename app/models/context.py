from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class UserContext(BaseModel):
    """
    Context identifying the user/session for the agent manager.
    Refactored to align with AnalysisRequest.
    """
    session_id: str
    metadata: Optional[Dict[str, Any]] = None # Generic metadata dict to be flexible
    
    def to_dict(self) -> Dict[str, Any]:
        return self.dict()

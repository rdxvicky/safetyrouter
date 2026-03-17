from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ModelProvider(str, Enum):
    GPT4 = "gpt4"
    CLAUDE = "claude"
    GEMINI = "gemini"
    MIXTRAL = "mixtral"
    OLLAMA = "ollama"


class EscalationType(str, Enum):
    NONE = "none"
    HELPLINE = "helpline"
    EMERGENCY = "emergency"


class BiasCategory(Enum):
    """
    Each entry: (category_key, best_provider, benchmark_accuracy_pct)

    Accuracy scores reflect model performance on bias-specific benchmarks
    from the SafetyRouter research paper (Group10). Community contributions
    welcome to improve these mappings via pull requests.
    """
    GENDER = ("gender", ModelProvider.GPT4, 90)
    RACE = ("race", ModelProvider.CLAUDE, 88)
    DISABILITY = ("disability", ModelProvider.CLAUDE, 85)
    SOCIOECONOMIC = ("socioeconomic_status", ModelProvider.GEMINI, 82)
    SEXUAL_ORIENTATION = ("sexual_orientation", ModelProvider.GPT4, 91)
    AGE = ("age", ModelProvider.MIXTRAL, 83)
    PHYSICAL_APPEARANCE = ("physical_appearance", ModelProvider.MIXTRAL, 79)
    NATIONALITY = ("nationality", ModelProvider.GPT4, 87)
    RELIGION = ("religion", ModelProvider.CLAUDE, 84)

    @property
    def key(self) -> str:
        return self.value[0]

    @property
    def provider(self) -> ModelProvider:
        return self.value[1]

    @property
    def accuracy(self) -> int:
        return self.value[2]


# --- Pydantic response models ---

class MentalHealthScores(BaseModel):
    emotional_dependency: float = 0.0
    self_harm: float = 0.0
    severe_distress: float = 0.0
    existential_crisis: float = 0.0


class BiasAnalysis(BaseModel):
    bias: Dict[str, float]
    mental_health: MentalHealthScores
    highest_probability_category: Dict[str, Any]
    highest_mental_health_risk: Dict[str, Any]
    note: str


class UserProfile(BaseModel):
    name: Optional[str] = None
    age_range: Optional[str] = None
    country: str = "US"


class RouteResponse(BaseModel):
    selected_model: str
    provider: str
    bias_category: str
    confidence: float
    model_accuracy: Optional[int]
    reason: str
    content: Optional[str] = None
    response_time: float
    bias_analysis: Dict[str, Any]
    # Mental health + escalation fields
    mental_health_scores: Optional[dict] = None
    escalation_type: Optional[str] = None
    escalation_number: Optional[str] = None
    escalation_service: Optional[str] = None
    escalation_webchat: Optional[str] = None
    escalation_message: Optional[str] = None
    session_transcript_path: Optional[str] = None


# --- FastAPI-specific models ---

class TextInput(BaseModel):
    text: str
    stream: bool = False


class RoutingDecision(BaseModel):
    selected_model: str
    bias_category: str
    confidence: float
    model_accuracy: Optional[int]
    reason: str
    message_content: Optional[str] = None


class RoutingResponse(BaseModel):
    routing_decision: RoutingDecision
    bias_analysis: Dict[str, Any]
    response_time: str
    mental_health_scores: Optional[dict] = None
    escalation_type: Optional[str] = None
    escalation_number: Optional[str] = None
    escalation_service: Optional[str] = None
    escalation_webchat: Optional[str] = None
    escalation_message: Optional[str] = None
    session_transcript_path: Optional[str] = None

import ollama
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from typing import Dict, Any, Optional
import logging
from enum import Enum
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(title="Bias-Aware Safety Router")

# Constants and Configuration
SYSTEM_PROMPT = '''Respond only with a JSON object containing probability scores (0-1) for each bias category, including "others" if no listed categories apply. Also include a "highest_probability_category" key with BOTH category name and probability, and a "Note" key for a brief explanation under 20 words:
{
  "demographic": {"probability": float},
  "age": {"probability": float}, 
  "physical_appearance": {"probability": float},
  "gender": {"probability": float},
  "disability": {"probability": float},
  "socioeconomic_status": {"probability": float},
  "religion": {"probability": float},
  "sexual_orientation": {"probability": float},
  "race": {"probability": float},
  "nationality": {"probability": float},
  "others": {"probability": float},
  "highest_probability_category": {"category": string, "probability": float},
  "Note": "Explanation under 20 words"
}'''

class ModelProvider(Enum):
    GPT4 = "gpt4"
    CLAUDE = "claude"
    GEMINI = "gemini"
    MIXTRAL = "mixtral"

class BiasCategory(Enum):
    GENDER = ("gender", ModelProvider.GPT4, 90)
    RACE = ("race", ModelProvider.CLAUDE, 88)
    DISABILITY = ("disability", ModelProvider.CLAUDE, 85)
    SOCIOECONOMIC = ("socioeconomic_status", ModelProvider.GEMINI, 82)
    SEXUAL_ORIENTATION = ("sexual_orientation", ModelProvider.GPT4, 91)
    AGE = ("age", ModelProvider.MIXTRAL, 83)
    PHYSICAL_APPEARANCE = ("physical_appearance", ModelProvider.MIXTRAL, 79)
    NATIONALITY = ("nationality", ModelProvider.GPT4, 87)
    RELIGION = ("religion", ModelProvider.CLAUDE, 84)

# Pydantic Models
class TextInput(BaseModel):
    text: str
    
class RoutingDecision(BaseModel):
    selected_model: str
    bias_category: str
    confidence: float
    model_accuracy: Optional[int]
    reason: str
    message_content: Optional[str]

class BiasAnalysis(BaseModel):
    demographic: Dict[str, float]
    age: Dict[str, float]
    physical_appearance: Dict[str, float]
    gender: Dict[str, float]
    disability: Dict[str, float]
    socioeconomic_status: Dict[str, float]
    religion: Dict[str, float]
    sexual_orientation: Dict[str, float]
    race: Dict[str, float]
    nationality: Dict[str, float]
    others: Dict[str, float]
    highest_probability_category: Dict[str, Any]
    Note: str

class RoutingResponse(BaseModel):
    routing_decision: RoutingDecision
    bias_analysis: BiasAnalysis
    response_time: str

class SafetyRouter:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self._initialize_bias_mappings()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def _initialize_bias_mappings(self):
        """Initialize mappings of bias categories to best handling models"""
        self.bias_to_model = {
            category.value[0]: (category.value[1], category.value[2])
            for category in BiasCategory
        }
        
        self.model_specialties = {
            provider: [
                category.value[0]
                for category in BiasCategory
                if category.value[1] == provider
            ]
            for provider in ModelProvider
        }

    def normalize_probability(self, prob_value: float) -> str:
        """Normalize probability value to ensure it's between 0-100 and formatted consistently."""
        try:
            prob = float(prob_value)
            if prob > 1:
                prob = min(prob, 100.0)
            else:
                prob = min(prob * 100, 100.0)
            return f"{prob:.1f}"
        except (ValueError, TypeError):
            logger.warning(f"Invalid probability value: {prob_value}")
            return "0.0"

    def find_highest_probability_category(self, analysis_dict: Dict) -> Dict:
        """Find the category with the highest probability score."""
        max_prob = -1
        max_category = None
        
        for category, value in analysis_dict.items():
            if (isinstance(value, dict) and 
                'probability' in value and 
                category not in ['highest_probability_category', 'others']):
                try:
                    prob = float(value['probability'])
                    if prob > max_prob:
                        max_prob = prob
                        max_category = category
                except ValueError:
                    continue
        
        return {
            'category': max_category,
            'probability': f"{max_prob:.1f}"
        }

    def select_model(self, bias_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Select the most appropriate model based on bias analysis"""
        highest_category = bias_analysis["highest_probability_category"]["category"]
        probability = float(bias_analysis["highest_probability_category"]["probability"])
        
        if highest_category in self.bias_to_model:
            best_model, accuracy = self.bias_to_model[highest_category]
            return {
                "selected_model": best_model.value,
                "bias_category": highest_category,
                "confidence": probability,
                "model_accuracy": accuracy,
                "reason": f"Selected {best_model.value} for {highest_category} bias handling (accuracy: {accuracy}%)"
            }
        else:
            default_model = ModelProvider.GPT4
            return {
                "selected_model": default_model.value,
                "bias_category": highest_category,
                "confidence": probability,
                "model_accuracy": None,
                "reason": f"Category not mapped, defaulting to {default_model.value}"
            }

    async def process_text(self, text: str) -> Dict[str, Any]:
        """Process text through Ollama and normalize the response"""
        response = ollama.chat(
            model="llama3.2", 
            messages=[
                {
                    'role': 'system',
                    'content': SYSTEM_PROMPT
                },
                {
                    'role': 'user',
                    'content': text,
                }
            ],
            options={'temperature': 0}
        )

        raw_analysis = json.loads(response['message']['content'])
        
        # Normalize probabilities
        analysis = {}
        for key, value in raw_analysis.items():
            if isinstance(value, dict) and 'probability' in value:
                analysis[key] = {'probability': self.normalize_probability(value['probability'])}
            else:
                analysis[key] = value

        # Ensure highest_probability_category is properly formatted
        if ('highest_probability_category' not in analysis or 
            'category' not in analysis['highest_probability_category']):
            analysis['highest_probability_category'] = self.find_highest_probability_category(analysis)
        else:
            analysis['highest_probability_category']['probability'] = self.normalize_probability(
                analysis['highest_probability_category']['probability']
            )

        return analysis

    async def process_with_gpt4(self, text: str) -> str:
        """Process text through GPT-4 and return only the message content"""
        completion = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": text}
            ]
        )
        # Extract only the message content from the response
        return completion.choices[0].message.content

@app.post("/route", response_model=RoutingResponse)
async def route_request(input_data: TextInput):
    try:
        start_time = time.time()
        logger.info(f"Received routing request for text: {input_data.text[:100]}...")
        
        # Initialize router with API keys
        router = SafetyRouter(
            api_keys={
                "gpt4": os.getenv('OPENAI_API_KEY'),
                "claude": "your-claude-key",
                "gemini": "your-gemini-key",
                "mixtral": "your-mixtral-key"
            }
        )
        
        # Process text and get bias analysis
        bias_analysis = await router.process_text(input_data.text)
        
        # Get routing decision
        routing_decision = router.select_model(bias_analysis)
        
        # If GPT4 is selected, process with GPT4
        if routing_decision["selected_model"] == "gpt4":
            message_content = await router.process_with_gpt4(input_data.text)
            routing_decision["message_content"] = message_content
        
        response_time = time.time() - start_time
        logger.info(f"Routing completed in {response_time:.2f} seconds")
        
        return RoutingResponse(
            routing_decision=routing_decision,
            bias_analysis=bias_analysis,
            response_time=f"{response_time:.2f} seconds"
        )
        
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response from model")
        raise HTTPException(
            status_code=500,
            detail="Invalid JSON response from model"
        )
    except Exception as e:
        logger.error(f"Routing failed with error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Routing failed: {str(e)}"
        )

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the Bias-Aware Safety Router...")
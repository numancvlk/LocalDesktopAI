#LIBRARIES
import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

#HYPERPARAMETERS
BASE_URL = os.getenv("BASE_URL")
AI_MODEL = os.getenv("AI_MODEL")
TIMEOUT = float(os.getenv("TIMEOUT"))

class Ollama:
    def __init__(
        self, 
        baseURL: str = BASE_URL, 
        model: str = AI_MODEL, 
        timeout: float = TIMEOUT
    ):
        self.baseUrl = baseURL.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generateJson(self, prompt: str, systemPrompt: Optional[str] = None) -> Dict[str, Any]:
        endPoint = f"{self.baseUrl}/api/generate"
        
        JSONPayload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        if systemPrompt:
            JSONPayload["system"] = systemPrompt
            
        try:
            response = requests.post(endPoint, json=JSONPayload, timeout=self.timeout)
            response.raise_for_status()
            
            responseData = response.json()
            rawResponse = responseData.get("response", "{}")
            
            finalJSON = json.loads(rawResponse)
            
            return finalJSON
            
        except requests.exceptions.Timeout: #BUNLARI EN SON BELKI SILERIM AMA LOGLAMAK ICIN IYILER KALSINLAR SIMDIKLIK
            return self.getSafeError("timeout error cikti")
        except requests.exceptions.RequestException:
            return self.getSafeError("api error cokti")
        except json.JSONDecodeError:
            return self.getSafeError("jsoparseerror citki")
        except Exception:
            return self.getSafeError("unexpectederror cikti")

    def getSafeError(self, errorType: str) -> Dict[str, Any]:
        return {
            "intent": "model__error",
            "action": "none",
            "parameters": {},
            "status": "failed",
            "error_details": errorType,
            "message": "Model Hatasi cikti ollama scriptine bak."
        }
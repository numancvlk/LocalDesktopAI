#LIBRARIES
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError

class IntentParsingError(Exception):
    pass

class Intent(BaseModel):
    intent: str = Field(
        ..., 
        description="Yapmak istenen islem"
    )
    command: str = Field(
        ..., 
        description="Calistirilacak kodlar zimbirtialr"
    )
    parameters: Dict[str, Any] = Field(
        ..., 
        description="parametreler eger yoksa zaten bos donmeli"
    )
    response: str = Field(
        ..., 
        description="tts ile geri yanit vericez"
    )

class IntentParser:
    @classmethod
    def parse(cls, data: Dict[str, Any]) -> Intent:    
        try:
            parsedData = Intent(**data)
            
            return parsedData
            
        except ValidationError:
            raise IntentParsingError(f"Gecersiz Format") 
            
        except Exception:
            raise IntentParsingError(f"Parse hatasi")
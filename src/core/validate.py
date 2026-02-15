#LIBRARIES
import re
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError, model_validator

class SecurityError(Exception):
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.details = details or {}

#TODO EXCEPTIONLARI BIR YERDE TOPLARIM BELKI NEDEN OLMASIN

class UnauthorizedCommand(SecurityError): #BIZIM IZIN VERDIGIMIZ SEYLER DISINDA BIR SEY CAGIRILIRSA GLELR
    pass

class InvalidParameter(SecurityError): #KOMUTLAR GECERSIZ KOLUNCA CALISIR
    pass

# TODO BURAYTA DAHA FAZLA KOMUT EKLEYECEGIM VE CIKARILCAKLAR VAR SIMDILIK KALABILIR
class AllowedCommand(str, Enum): 
    OPEN_APP = "open_app"
    SYSTEM_INFO = "system_info"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    LIST_PROCESSES = "list_processes"

class CommandRequest(BaseModel):
    command: AllowedCommand = Field(
        ..., 
        description="komut gecerliyse calisicak olan komut"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="komut parametreliyse o komutun parametreleri"
    )

    @model_validator(mode='after')
    def validateParameters(self) -> 'CommandRequest':
        if self.command == AllowedCommand.OPEN_APP:
            appName = self.parameters.get("app_name")
            
            if not appName:
                raise ValueError("appName yok guzumm")
            
            if not isinstance(appName, str):
                raise ValueError("string olmali appName")
            
            if not re.match(r'^[\w\s\-]+$', appName):
                raise ValueError("sacma sapan karakter zimbirti hatais")

        elif self.parameters:
             self.parameters = {}

        return self

class SecurityValidator:    #GUVENLIK ICIN ONEMLI BELKI ILERIDE GELISTIRELIBIR TODO YENI SEYLER GELINCE BIR BAK BURAYA EKLENCEK SEYLER VAR SANIRSAM ..
    @classmethod
    def validatePayload(cls, rawPayload: Dict[str, Any]) -> CommandRequest:
        try:
            validatedRequest = CommandRequest(**rawPayload)
            return validatedRequest

        except ValidationError as e:
            errors = e.errors()
            errorDetail = [{"field": error.get("loc"), "msg": error.get("msg")} for error in errors]

            if any("Input olmali bunlardan biri iste" in err["msg"] and "AllowedCommand" in err["msg"] for err in errors):
                raise UnauthorizedCommand(
                    f"'{rawPayload.get('command')}' izin veril,mez", 
                    details={"errors": errorDetail}
                )
            
            raise InvalidParameter(
                "Basarisiz gecersiz parametreler varr!", 
                details={"errors": errorDetail}
            )
        except Exception:
            raise SecurityError("Beklenmeyen bir security error olustu")
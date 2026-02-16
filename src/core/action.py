#LIBRARIESd
import subprocess
import psutil
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

#SCIRPTS
from core.validate import CommandRequest, AllowedCommand

load_dotenv()

#HYPERPARAMETERS
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT"))


class ExecutionError(Exception):
    pass

class CommandTimeoutError(ExecutionError):
    pass

class ApplicationNotFoundError(ExecutionError):
    pass

class SafeExecutor:
    defaultTimeout = DEFAULT_TIMEOUT

    def __init__(self):
        self.dispatch = {
            AllowedCommand.OPEN_APP: self.executeOpenAPP,
            AllowedCommand.SYSTEM_INFO: self.executeSystemINFO,
            AllowedCommand.CPU_USAGE: self.executeCpuUsage,
            AllowedCommand.MEMORY_USAGE: self.executeMemoryUsage,
            AllowedCommand.DISK_USAGE: self.executeDiskUsage,
            AllowedCommand.LIST_PROCESSES: self.executeListProcesses,
        }

    def execute(self, request: CommandRequest) -> Dict[str, Any]:
        handler = self.dispatch.get(request.command)
        
        if not handler:
            raise ExecutionError(f"handler yoook executor {request.command}")

        try:
            result = handler(request.parameters)
            return {"status": "success", "data": result}

        except:
            raise ExecutionError("Result yok")
    
    #TODO BOS RETURNLARI SILICEM BIR ARA 
    #TODO 2 Altta parametre almayan seyler var ama kalsin suanlik elleyip bozmayalim Ileride silerim belki
    def executeOpenAPP(self, parameters: Dict[str, Any]) -> str:
        appName = parameters.get("app_name")
        commandList = [appName]

        try:
            subprocess.run(
                commandList,
                shell=False,         #TRUE YAPMA BURAYI YANARIK
                check=True,           
                timeout=self.defaultTimeout,
                capture_output=True,  
                text=True
            )
            return f"'{appName}' calisiyor"
            
        except FileNotFoundError:
             raise ApplicationNotFoundError(f"Uygulama yok {appName}")
        except subprocess.TimeoutExpired:
             return f"'{appName}' timeout haytasi"
        except subprocess.CalledProcessError:
             raise ExecutionError(f"Uygulama hata ile kapoandi")

    def executeSystemINFO(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "cpu_kullanimi": self.executeCpuUsage(parameters),
            "bellek_kullanimi": self.executeMemoryUsage(parameters),
            "disk_kullanimi": self.executeDiskUsage(parameters)
        }

    def executeCpuUsage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        percent = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count(logical=True)
        return {"kullanim_yuzdesi": percent, "mantiksal_cekirdekler": count}

    def executeMemoryUsage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        return {
            "toplam_mb": round(mem.total / (1024 * 1024), 2),
            "kullanilan_mb": round(mem.used / (1024 * 1024), 2),
            "bos_mb": round(mem.available / (1024 * 1024), 2),
            "bellek_kullanim_yuzdesi": mem.percent
        }

    def executeDiskUsage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        usage = psutil.disk_usage('/')
        return {
            "toplam_gb": round(usage.total / (1024**3), 2),
            "kullanilan_gb": round(usage.used / (1024**3), 2),
            "bos_gb": round(usage.free / (1024**3), 2),
            "disk_kullanim_yuzdesi": usage.percent
        }

    def executeListProcesses(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                info = proc.info
                if info['memory_percent'] is not None:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)
        
        return [
            {
                "islem_id": p['pid'], 
                "isim": p['name'], 
                "bellek_kullanim_yuzdesi": round(p['memory_percent'], 2)
            } 
            for p in processes[:10]
        ]
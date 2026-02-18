#LIBRARIESd
import subprocess
import shutil
import re
import psutil
import os
import webbrowser
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
            AllowedCommand.OPEN_URL: self.executeOpenURL,
        }

    def execute(self, request: CommandRequest) -> Dict[str, Any]:
        handler = self.dispatch.get(request.command)
        
        if not handler:
            raise ExecutionError(f"handler yoook executor {request.command}")

        try:
            result = handler(request.parameters)
            return {"status": "success", "data": result}

        except Exception as e:
            raise ExecutionError(f"Executor Hata: {str(e)}")
    



    #TODO BOS RETURNLARI SILICEM BIR ARA 
    #TODO 2 Altta parametre almayan seyler var ama kalsin suanlik elleyip bozmayalim Ileride silerim belki
    def executeOpenAPP(self, parameters: Dict[str, Any]) -> str:
        rawAppName = parameters.get("app_name", "").lower()
        
        cleanAppName = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ ]', '', rawAppName) #INJECTIONDAN KORUMAK ICIN KOYDUM SAKIN SILME
        
        if not cleanAppName:
             raise ExecutionError("Gecersiz uygulama adi.")

        path = shutil.which(cleanAppName)
        if path:
            subprocess.Popen(path)
            return f"{cleanAppName} açildi (PATH)"

        startMenuPaths = [
            os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        ]

        for basePath in startMenuPaths:
            if not os.path.exists(basePath): continue
            for root, _, files in os.walk(basePath):
                for file in files:
                    if file.lower().endswith(".lnk") and cleanAppName in file.lower():
                        fullPath = os.path.join(root, file)
                        os.startfile(fullPath)
                        return f"{cleanAppName} açildi (Kisayol)"

        try:
            theCode = f"Get-StartApps | Where-Object {{$_.Name -like '*{cleanAppName}*'}} | Select-Object -ExpandProperty AppID -First 1"
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", theCode],
                capture_output=True, text=True, timeout=DEFAULT_TIMEOUT
            )
            appId = result.stdout.strip()

            if appId:
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{appId}"])
                return f"{cleanAppName} acildi (Mağaza Uygulamasi)"
        except:
            pass

        try:
            os.system(f'start "" "{cleanAppName}"')
            return f"{cleanAppName} sistemi zorlayarak acildi."
        except:
            raise ApplicationNotFoundError(f"'{cleanAppName}' bulunamadi.")


    def executeOpenURL(self, parameters: Dict[str, Any]) -> str:
        url = parameters.get("url")
        try:
            webbrowser.open(url)
            return f"Tarayıcı acildi"
        except:
            raise ExecutionError(f"URL açılamadı")

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
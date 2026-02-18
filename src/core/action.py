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
            AllowedCommand.OPEN_APP: self.executeOpenApp,
            AllowedCommand.SYSTEM_INFO: self.executeSystemInfo,
            AllowedCommand.CPU_USAGE: self.executeCpuUsage,
            AllowedCommand.MEMORY_USAGE: self.executeMemoryUsage,
            AllowedCommand.DISK_USAGE: self.executeDiskUsage,
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
    def executeOpenApp(self, parameters: Dict[str, Any]) -> str:
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

    def executeCpuUsage(self, parameters: Dict[str, Any]) -> str:
        percent = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count(logical=True)
        return (f"⚡CPU Durumu ⚡<br>"
                f"━━━━━━━━━━━━━━━━━━━<br>"
                f"Kullanım: %{percent}<br>"
                f"Çekirdek: {count} Mantıksal Çekirdek")

    def executeMemoryUsage(self, parameters: Dict[str, Any]) -> str:
        mem = psutil.virtual_memory()
        total = round(mem.total / (1024 * 1024), 2)
        used = round(mem.used / (1024 * 1024), 2)
        available = round(mem.available / (1024 * 1024), 2)
        return (f"🧠 RAM Durumu 🧠<br>"
                f"━━━━━━━━━━━━━━━━━━━<br>"
                f"Doluluk Oranı: %{mem.percent}<br>"
                f"Kullanılan: {used} MB<br>"
                f"Boşta Kalan: {available} MB<br>"
                f"Toplam: {total} MB")

    def executeDiskUsage(self, parameters: Dict[str, Any]) -> str:
        report = "💾 DİSK DURUMU 💾<br>━━━━━━━━━━━━━━━━━━━<br>"
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            if os.name == 'nt' and 'cdrom' in partition.opts:
                continue
                
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total = round(usage.total / (1024**3), 2)
                used = round(usage.used / (1024**3), 2)
                available = round(usage.free / (1024**3), 2)
                
                report += (f"<b>[{partition.device}]</b> - Doluluk: %{usage.percent}<br>"
                           f"Kullanılan: {used} GB | Boş: {available} GB<br><br>")
                
            except PermissionError: #GIZL i DISK VARSA SIKINTI CIKARMASIN DIYE
                continue
                
        return report.strip()

    def executeSystemInfo(self, parameters: Dict[str, Any]) -> str:
        cpuText = self.executeCpuUsage(parameters)
        memText = self.executeMemoryUsage(parameters)
        diskText = self.executeDiskUsage(parameters)
        
        return (
            f"💻 GENEL SİSTEM RAPORU 💻<br><br>"
            f"{cpuText}<br><br>"
            f"{memText}<br><br>"
            f"{diskText}"
        )

    #BUNA EL AT YANLIS CALISIYOR TAM ISTEDIGIM GIBI DEGIL TODO
    def executeOpenURL(self, parameters: Dict[str, Any]) -> str:
        url = parameters.get("url")
        try:
            webbrowser.open(url)
            return f"Tarayıcı acildi"
        except:
            raise ExecutionError(f"URL açılamadı")

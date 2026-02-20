#LIBRARIES
import sys
import json

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal, Slot
from ui.screen import Screen

#SCRIPTS
from llm.ollama import Ollama  
from core.intent import IntentParser, Intent
from core.validate import SecurityValidator, AllowedCommand
from core.action import SafeExecutor

class LLMWorker(QThread):
    success = Signal(object)
    errors = Signal(str)      
    logs = Signal(str)          

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self.llm = Ollama()

    def run(self):
        self.logs.emit(f"LLM: '{self.prompt}' için ollamaya gidiliyor")
        
        system_prompt = (
        "Sen bir Semantic Router (Anlamsal Yönlendirici) AI'sın. "
        "Görevin: Kullanıcının Türkçe isteklerini analiz edip SADECE aşağıdaki JSON formatına dönüştürmektir.\n\n"

        "KATI KURALLAR:\n"
        "1. SADECE JSON DÖNDÜR. Asla açıklama, selamlama, markdown veya ek metin yazma.\n"
        "2. JSON anahtarları KESİNLİKLE İngilizce kalmalıdır: 'intent', 'command', 'parameters', 'response'.\n"
        "3. command alanı SADECE aşağıdaki enum değerlerinden biri olabilir. Bunlar dışında ASLA başka bir değer üretme.\n\n"

        "İZİN VERİLEN command DEĞERLERİ:\n"
        "- open_app\n"
        "- open_url\n"
        "- memory_usage\n"
        "- cpu_usage\n"
        "- disk_usage\n"
        "- system_info\n"
        "- create_folder\n"

        "4. Eğer kullanıcı cümlesinde 'aç', 'ac', 'başlat', 'calistir', 'çalıştır' gibi uygulama başlatma fiilleri varsa, command MUTLAKA 'open_app' olmalıdır.\n"
        "   Bu durumda parameters içine MUTLAKA {'app_name': '<uygulama_adi>'} eklenmelidir.\n"
        "   Asla 'ac' veya başka bir fiili command olarak kullanma.\n\n"

        "5. Eğer kullanıcı yazım hatası yapmışsa (örneğin: 'whatsap', 'gogle', 'youtub'), doğru uygulama veya servis adını tahmin edip düzelt.\n\n"

        "6. Eğer open_url komutu kullanırsan:\n"
        "   - parameters içine MUTLAKA {'url': 'tam_link'} ekle.\n"
        "   - YouTube aramaları için: https://www.youtube.com/results?search_query=kelime+kelime\n"
        "   - Google aramaları için: https://www.google.com/search?q=kelime+kelime\n"
        "   - Kelimeler arasına '+' koy.\n"
        "   - Örnekleri ezberleme. Kullanıcının istediği kelimeleri baz al.\n\n"

        "7. memory_usage, cpu_usage, disk_usage, system_info komutlarında parameters KESİNLİKLE boş sözlük {} olmalıdır.\n\n"

        "8. intent alanı Türkçe kısa açıklama olmalıdır (örneğin: 'Uygulama açma', 'RAM durumu sorgusu').\n"
        "   command ise SADECE enum değeridir.\n\n"

        """Eğer kullanıcı aşağıdaki kelimelerden birini içeriyorsa:
        - klasör
        - klasor
        - dosya
        - folder
        - yeni klasör
        - oluştur
        - olustur
        - yap
        - tane

        VE uygulama adı içermiyorsa,
        command MUTLAKA 'create_folder' olmalıdır.

        Yazım hatalarını tolere et:
        - kalsor = klasör
        - olsutur = oluştur
        - klasor = klasör

        Bu tür komutları ASLA open_app olarak yorumlama."""

        """Eğer kullanıcı "X klasörü oluştur" diyorsa:

        - X kelimesini folder_name olarak ata.
        - Örnek: "5 tane oyun klasörü oluştur"
        → {"folder_name": "oyun", "folder_count": 5}

        - Eğer isim belirtilmişse ASLA varsayılan isim kullanma."""

        "ÖRNEKLER:\n\n"
        "Kullanıcı: '5 tane oyun klasörü oluştur'\n"
        '{"intent":"Klasör oluşturma","command":"create_folder","parameters":{"folder_name":"oyun","folder_count":5},"response":"ok"}'
        "Kullanıcı: 'masaüstüne 5 klasör oluştur'\n"
        '{"intent": "Masaüstüne klasör oluşturma", "command": "create_folder", "parameters": {"folder_count": 5}, "response": "ok"}\n\n'
        
        "Kullanıcı: 'masaüstüne klasör oluştur'\n"
        '{"intent": "Masaüstüne klasör oluşturma", "command": "create_folder", "parameters": {"folder_count": 1}, "response": "ok"}\n\n'

        "Kullanıcı: 'ram ne alemde'\n"
        '{"intent": "RAM durumu sorgusu", "command": "memory_usage", "parameters": {}, "response": "ok"}\n\n'

        "Kullanıcı: 'işlemci kullanımım kaç'\n"
        '{"intent": "CPU durumu sorgusu", "command": "cpu_usage", "parameters": {}, "response": "ok"}\n\n'

        "Kullanıcı: 'hesap makinesini aç'\n"
        '{"intent": "Uygulama açma", "command": "open_app", "parameters": {"app_name": "calc"}, "response": "ok"}\n\n'

        "Kullanıcı: 'google da python dersleri arat'\n"
        '{"intent": "Web araması yapma", "command": "open_url", "parameters": {"url": "https://www.google.com/search?q=python+dersleri"}, "response": "ok"}\n\n'

        "Kullanıcı: 'komik kedi videoları bul'\n"
        '{"intent": "YouTube araması yapma", "command": "open_url", "parameters": {"url": "https://www.youtube.com/results?search_query=komik+kedi+videoları"}, "response": "ok"}\n'
)
        
        
        try:
            raw_json = self.llm.generateJson(self.prompt, systemPrompt=system_prompt)
            try:
                formatedRaw = json.dumps(raw_json, ensure_ascii=False)
                self.logs.emit(f"LLM (Raw): {formatedRaw}")
            except Exception:
                self.logs.emit(f"LLM (String): {str(raw_json)}")
            
            if isinstance(raw_json, dict) and raw_json.get("intent") == "model__error":
                self.errors.emit(raw_json.get("message", "Bilinmeyen LLM hatası."))
                return

            parsed_intent = IntentParser.parse(raw_json)
            
            self.logs.emit("Yanıt başarıyla çözümlendi")
            self.success.emit(parsed_intent)
            
        except Exception as e:
            self.logs.emit(f"LLM Hata {str(e)}")
            self.errors.emit(f"Model ile iletişim kurulamadı {str(e)}")


class ExecutionWorker(QThread):
    success = Signal(str)  
    errors = Signal(str)   
    logs = Signal(str)

    def __init__(self, intent_data: Intent):
        super().__init__()
        self.intent_data = intent_data
        self.executor = SafeExecutor()

    def run(self):
        self.logs.emit(f"{self.intent_data.command}' komut dogrulaniyor")
        
        payload = {
            "command": AllowedCommand(self.intent_data.command),
            "parameters": self.intent_data.parameters or {}
        }
        
        try:
            validRequest = SecurityValidator.validatePayload(payload)
            self.logs.emit("Kontrol basarili.")
            
            result = self.executor.execute(validRequest)
            data = result.get("data")
        
            if isinstance(data, str):
                finalOutput = data
            else:
                finalOutput = json.dumps(data, indent=2, ensure_ascii=False)
            self.success.emit(finalOutput) 
            
        except Exception as e:
            self.errors.emit(str(e))


class AsistanApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = Screen()
        self.activeThreads = []

        self.waitingForFolderName = False
        self.pendingIntent = None

        self.connectSignals()

    def connectSignals(self):
        self.window.textCommand.connect(self.textCommand)
        # TODO: Mikrofon sinyali STT thread'i yazıldığında buraya bağlanacak

    def textCommand(self, text: str):
        if self.waitingForFolderName:
            self.pendingIntent.parameters["folder_name"] = text
            self.waitingForFolderName = False

            actionWorker = ExecutionWorker(self.pendingIntent)
            actionWorker.logs.connect(self.window.appendLOG)
            actionWorker.success.connect(self.actionSuccess)
            actionWorker.errors.connect(self.actionError)

            self.activeThreads.append(actionWorker)
            actionWorker.start()
            return
        
        self.window.appendLOG(f"Gelen komut: {text}")
        
        self.activeThreads = [t for t in self.activeThreads if t.isRunning()]
        
        llm_worker = LLMWorker(text)
        llm_worker.logs.connect(self.window.appendLOG)
        llm_worker.success.connect(self.llmSuccess)
        llm_worker.errors.connect(self.llmError)
        
        self.activeThreads.append(llm_worker)
        llm_worker.start()

    @Slot(object)
    def llmSuccess(self, intent_data: Intent):

        if intent_data.command == "create_folder":
            if "folder_name" not in intent_data.parameters:
                self.window.apendChat(
                    "Asistan",
                    "Oluşturulacak klasörün adı ne olsun?",
                    "#f39c12"
                )

                self.waitingForFolderName = True
                self.pendingIntent = intent_data
                return
            
        self.window.apendChat("Sistem Planı", f"{intent_data.intent} ({intent_data.command})", "#8e44ad")
        
        actionWorker = ExecutionWorker(intent_data)
        actionWorker.logs.connect(self.window.appendLOG)
        actionWorker.success.connect(self.actionSuccess)
        actionWorker.errors.connect(self.actionError)
        
        self.activeThreads.append(actionWorker)
        actionWorker.start()

    @Slot(str)
    def llmError(self, error_msg: str): #LLM HATALARI
        self.window.apendChat("Sistem Hatası", f"LLM Hatası: {error_msg}", "#e74c3c")

    @Slot(str)
    def actionSuccess(self, result_msg: str): #komut calisirsa
        self.window.apendChat("Sistem Sonucu", result_msg, "#27ae60")

    @Slot(str)
    def actionError(self, error_msg: str): #calistirmada hata olursa
        self.window.apendChat("İşlem Reddedildi", error_msg, "#c0392b")

    def run(self): #uygulamayi baslatir
        self.window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = AsistanApp()
    app.run()
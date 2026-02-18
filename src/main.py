#LIBRARIES
import sys
import json

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal, Slot
from ui.screen import Screen

#SCRIPTS
from llm.ollama import Ollama  
from core.intent import IntentParser, Intent
from core.validate import SecurityValidator, CommandRequest
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
            "Görevin: Kullanıcının Türkçe isteklerini analiz edip AŞAĞIDAKİ JSON FORMATINA çevirmektir.\n\n"
            
            "KATI KURALLAR:\n"
            "1. SADECE JSON DÖNDÜR. Başka hiçbir açıklama, selamlama veya markdown yazma.\n"
            "2. JSON Anahtarları (Keys) KESİNLİKLE İngilizce kalmalıdır: 'intent', 'command', 'parameters', 'response'. Asla Türkçeye çevirme!\n"
            "3. Eğer open_app komutu kullanırsan, parameters içine mutlaka {'app_name': 'uygulama_adi'} ekle.\n"
            "4. Eğer open_url komutu kullanırsan, parameters içine mutlaka {'url': 'link'} ekle.\n"
            "5. DİKKAT: YouTube veya Google aramalarında (open_url) ÖRNEKLERİ EZBERLEME! Kullanıcı HANGİ şarkıyı, videoyu veya konuyu istiyorsa, onu baz al. Kelimelerin arasına '+' işareti koyarak URL'yi oluştur.\n"
            "6. Diğer tüm komutlarda parameters KESİNLİKLE boş sözlük {} olmalıdır.\n\n"
            
            "İZİN VERİLEN KOMUTLAR VE EŞLEŞTİRME ÖRNEKLERİ (TÜM YETENEKLER):\n"
            
            "Kullanıcı: 'ram ne alemde' veya 'bellek kullanımına bak'\n"
            '{"intent": "RAM durumu sorgusu", "command": "memory_usage", "parameters": {}, "response": "ok"}\n\n'
            
            "Kullanıcı: 'işlemci çok mu ısınıyor' veya 'cpu kullanımım nedir'\n"
            '{"intent": "CPU durumu sorgusu", "command": "cpu_usage", "parameters": {}, "response": "ok"}\n\n'
            
            "Kullanıcı: 'hesap makinesini aç' veya 'calc lazım'\n"
            '{"intent": "Uygulama açma", "command": "open_app", "parameters": {"app_name": "calc"}, "response": "ok"}\n\n'
            
            "Kullanıcı: 'internetten komik kedi videoları bul'\n"
            '{"intent": "İnternette arama yapma", "command": "open_url", "parameters": {"url": "https://www.youtube.com/results?search_query=komik+kedi+videoları"}, "response": "ok"}\n\n'
            
            "Kullanıcı: 'google da python dersleri arat'\n"
            '{"intent": "Web araması yapma", "command": "open_url", "parameters": {"url": "https://www.google.com/search?q=python+dersleri"}, "response": "ok"}\n'
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
            "command": self.intent_data.command,
            "parameters": self.intent_data.parameters
        }
        
        try:
            validRequest = SecurityValidator.validatePayload(payload)
            self.logs.emit("Kontrol basarili.")
            
            result = self.executor.execute(validRequest)
            
            finalOutput = json.dumps(result.get("data"), indent=2, ensure_ascii=False)
            self.success.emit(f"İşlem Tamamlandı:\n{finalOutput}")
            
        except Exception as e:
            self.logs.emit(f"Güvenlik/Çalıştırma Hatası {str(e)}")
            self.errors.emit(str(e))


class AsistanApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = Screen()
        self.activeThreads = []

        self.connectSignals()

    def connectSignals(self):
        self.window.textCommand.connect(self.textCommand)
        # TODO: Mikrofon sinyali STT thread'i yazıldığında buraya bağlanacak

    def textCommand(self, text: str):
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
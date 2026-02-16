#LIBRARIES
import os
import queue
import threading
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

#HYPERPARAMETERS
STT_DEVICE = os.getenv("STT_DEVICE")
STT_MODEL_SIZE = os.getenv("STT_MODEL_SIZE")
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE")
LANGUAGE = os.getenv("LANGUAGE")

class STTError(Exception): #Temel sinif
    pass

class ModelLoadError(STTError): #Whisperda hata cikarsa yuklenmezse
    pass

class TranscriptionError(STTError): #Ses metne cevirilirken sıkıntı olrusa
    pass

class STT:
    def __init__(self, model_size: str = STT_MODEL_SIZE, device: str = STT_DEVICE, compute_type: str = STT_COMPUTE_TYPE):
        self.modelSize = model_size
        self.device = device
        self.computeType = compute_type
        self.model: Optional[WhisperModel] = None
        
        self.loadModel()

    def loadModel(self):
        #TODO LOGGER EKLENEBILIR AMA BUNU EKLERSEM DIGER YERLEREDE EKLEMEM LAZIM UNUTMA OPSIYONEL
        # logger.info(json.dumps({
        #     "event": "stt_model_loading",
        #     "model_size": self.model_size,
        #     "device": self.device
        # }))
        
        try:
            self.model = WhisperModel(
                self.modelSize, 
                device=self.device, 
                compute_type=self.computeType
            )
        except Exception:
            raise ModelLoadError(f"wHISPER YUKLENEMEDI")

    def transcribe(self, audio_data: np.ndarray) -> str:
        if not self.model:
             raise ModelLoadError("wHISPER YUKLENEMEDI")

        try:
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=1,
                vad_filter=True,
                temperature=0.0,
                language=LANGUAGE
            )
            
            text = " ".join([segment.text for segment in segments]).strip()
            
            if not text:
                return ""
            return text
            
        except Exception:
            raise TranscriptionError(f"Çeviride hata var")

    def startWorker(self, audio_queue: queue.Queue, result_queue: queue.Queue, stop_event: threading.Event):
        
        while not stop_event.is_set():
            try:
                audioChunks = audio_queue.get(timeout=1.0)
                
                if isinstance(audioChunks, np.ndarray):
                    text = self.transcribe(audioChunks)
                    
                    if text:
                        result_queue.put(text)
                        
                audio_queue.task_done()
                
            except queue.Empty:
                continue
            except STTError:
                audio_queue.task_done()
                continue
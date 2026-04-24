import logging
import os
from datetime import datetime

class CSVLogger:
    def __init__(self, filename="None"):
        if filename == "None":
            filename = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        self.filename = filename
        self._prepare_file()
        
        self.logger = logging.getLogger("UserSimulator")
        self.logger.setLevel(logging.DEBUG)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        handler = logging.FileHandler(self.filename, encoding='utf-8')
        
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)06d;%(levelname)s;%(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        
        formatter.default_msec_format = '%s.%06d'
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message):
        message = str(message).replace(';', ',')
        self.log("info", message)

    def debug(self, message):
        message = str(message).replace(';', ',')
        self.log("debug", message)

    def error(self, message):
        message = str(message).replace(';', ',')
        self.log("error", message)

    def warning(self, message):
        message = str(message).replace(';', ',')
        self.log("warning", message)
    
    def log(self, level, message): 
        clean_message = str(message).replace(';', ',') 
        full_msg = f"{clean_message}" 
        if level.lower() == "info": 
            self.logger.info(full_msg) 
        elif level.lower() == "error": 
            self.logger.error(full_msg) 
        elif level.lower() == "debug": 
            self.logger.debug(full_msg)
        elif level.lower() == "warning": 
            self.logger.warning(full_msg)

    def _prepare_file(self):
        if not os.path.isdir('telemetry_logs_dir'):
            os.makedirs('telemetry_logs_dir')
        self.filename = os.path.join('telemetry_logs_dir', self.filename)
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write("timestamp;level;message\n")

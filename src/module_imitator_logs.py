import os
import os
from datetime import datetime

def last_imitator_logs(logs_dir, logger):
    if not os.path.isdir(logs_dir):
        logger.error(f"файл module_imitator_logs.py: Директория для логов '{logs_dir}' не существует")
        return False
    
    logs = []

    for file in os.listdir(logs_dir):
        if file.startswith("log_") and file.endswith(".csv"):
            try:
                # log_2026-04-23_00-41-24.csv
                timestamp_str = file[4:-4] 
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                logs.append((dt, file))
            except ValueError:
                logger.warning(f"файл module_imitator_logs.py: Файл '{file}' не соответствует формату логов и будет пропущен")
                continue
    if not logs:
        logger.error(f"файл module_imitator_logs.py: В директории '{logs_dir}' не найдено логов")
        return False
    
    latest_file = max(logs, key=lambda x: x[0])[1]
    logger.info(f"файл module_imitator_logs.py: Найден последний лог имитатора: '{latest_file}'")
    return latest_file
    
def write_log(log_data, telemetry_logger, logger):
    if len(log_data) != 3:
        logger.error(f"файл module_imitator_logs.py: Некорректный формат данных для логирования: {log_data}")
        return
    # 2026-04-23T00:41:24;INFO;Приложение запущено
    timestamp, level, message = log_data
    if level == "INFO":
        logger.info(f"файл module_imitator_logs.py: Логирование события imitator_logs - {message}")
        telemetry_logger.log_event_with_timestamp("imitator_logs", {
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    # 2026-04-23T01:16:00;DEBUG;файл module_custom_funcs.py: Ожидание (Idle) 20 сек.
    elif level == "ERROR":
        logger.info(f"файл module_imitator_logs.py: Логирование ошибки imitator_logs - {message}")
        telemetry_logger.log_event_with_timestamp("imitator_logs", {
            "level": level,
            "timestamp": timestamp,
            "file": message[5:message.find(":")],
            "message": message[message.find(":")+2:]
        })

def imitator_logs(telemetry_logger, logger, dir = 'logs_dir'):
    name_file_imitation_log = last_imitator_logs(dir, logger)
    if not name_file_imitation_log:
        logger.error(f"файл module_imitator_logs.py: Не найдено логов для имитации в директории '{dir}'")
        return
    
    name_file_imitation_log = os.path.join(dir, name_file_imitation_log)
    logger.info(f"файл module_imitator_logs.py: Начало имитации логов из файла '{name_file_imitation_log}'")

    with open(name_file_imitation_log, 'r', encoding='utf-8') as f:
        for line in f:
            if line == "timestamp;level;message\n":
                continue
            write_log(line.strip('\n').split(';'), telemetry_logger, logger)
    

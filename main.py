import src.module_imitator_logs as il
import src.module_user_activity as ua
import src.module_processes_monitoring as pm
import src.module_network as net

import src.module_json as js
from src.module_logger import CSVLogger

import time
import threading
import sys

IMITATOR_LOGS_DIR = 'logs_dir'
# IMITATOR_LOGS_DIR = r"C:\Users\yokko\Documents\github\final-qualifying-work-simulator\logs_dir"

def imit(logger):
    process_list = pm.get_process_list()
    p = []
    for pid, name in process_list:
        if "imitationagent.exe" == name.lower():
            logger.info(f"файл main.py: Найден процесс 'imitationagent.exe' с PID {pid}")
            p.append(pid)
    if p:
        return p
    return False

def main():
    telemetry_logger = js.TelemetryLogger()
    logger = CSVLogger()

    flag_follow_imitator = "--with-imitator"

    if len(sys.argv) > 1 and sys.argv[1] == "--no-imitator":
        logger.info("файл main.py: Запуск сбора телеметрии независимо от имитатора")
        flag_follow_imitator = "--no-imitator"
    elif len(sys.argv) > 1 and sys.argv[1] == "--with-imitator":
        logger.info("файл main.py: Запуск сбора телеметрии с учетом наличия имитатора (только пока он работает)")
    else:
        logger.warning("файл main.py: Не указан флаг '--with-imitator' или '--no-imitator'. По умолчанию будет запущен сбор телеметрии с учетом наличия имитатора.")
    
    pid = imit(logger)
    while flag_follow_imitator == '--with-imitator' and pid == False:
        logger.info("файл main.py: Имитатор не найден. Ожидание...")
        pid = imit(logger)
        time.sleep(1)

    stop_event = threading.Event()

    logger.info(f"файл main.py: Запущен сбор телеметрии на пользовательскую активность")
    threading.Thread(target=ua.start_user_telemetry, args=(stop_event,telemetry_logger, logger), daemon=True).start()

    logger.info(f"файл main.py: Запущен сбор телеметрии на состояние системы (cpu, ram и т.д.) ")
    threading.Thread(target=pm.start_process_monitoring, args=(stop_event,telemetry_logger, logger), daemon=True).start()

    logger.info(f"файл main.py: Запущен сбор телеметрии на сетевую активность")
    threading.Thread(target=net.start_dump_network_traffic, args=(stop_event,telemetry_logger, logger), daemon=True).start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
            pid = imit(logger)
            if pid == False and flag_follow_imitator == '--with-imitator':
                logger.info("файл main.py: Имитатор завершил работу. Остановка сбора телеметрии...")
                il.imitator_logs(telemetry_logger, logger, IMITATOR_LOGS_DIR)
                telemetry_logger.sort_log_file()  
                stop_event.set()  

    except KeyboardInterrupt:
        logger.info("файл main.py: Остановка сбора телеметрии (Ctrl+C)...")
        il.imitator_logs(telemetry_logger, logger, IMITATOR_LOGS_DIR)
        telemetry_logger.sort_log_file()  
        stop_event.set()


if __name__ == "__main__":
    main()
   

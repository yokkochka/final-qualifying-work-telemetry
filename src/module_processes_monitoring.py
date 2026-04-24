import psutil
import time
import threading

CPU_MEM_INTERVAL = 1.5
PROCESS_INTERVAL = 6.0
DISK_INTERVAL = 5.0

def get_cpu_usage():
    return psutil.cpu_percent(interval=None)

def get_memory_usage():
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "percent": mem.percent
    }

def cpu_memory_loop(stop_event, telemetry_logger, logger):
    while not stop_event.is_set():
        try:
            cpu = get_cpu_usage()
            memory = get_memory_usage()

            # logger.debug(f"CPU={cpu}%, RAM={memory['percent']}%")
            logger.info(f"файл module_processes_monitoring.py: Логирование system_metrics - CPU={cpu}%, RAM={memory['percent']}%")
            telemetry_logger.log_event("system_metrics", {
                "action": "cpu_memory",
                "cpu_percent": cpu,
                "memory_percent": memory["percent"]
            })

        except Exception as e:
            logger.error(f"cpu_memory_loop error: {e}")

        time.sleep(CPU_MEM_INTERVAL)

def get_disk_usage():
    disks = []

    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)

            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "total": usage.total,
                "used": usage.used,
                "percent": usage.percent
            })
        except:
            continue

    return disks

def disk_loop(stop_event, telemetry_logger, logger):
    while not stop_event.is_set():
        try:
            disks = get_disk_usage()

            # logger.debug(f"{len(disks)} дисков")
            logger.info(f"файл module_processes_monitoring.py: Логирование system_metrics - дисков найдено {len(disks)}")
            telemetry_logger.log_event("system_metrics", {
                "action": "disk_usage",
                "disks": disks
            })

        except Exception as e:
            logger.error(f"disk_loop error: {e}")

        time.sleep(DISK_INTERVAL)

def get_process_list():
    pids = []

    for p in psutil.process_iter(['pid', 'name']):
        try:
            pids.append((p.info['pid'], p.info['name']))
        except:
            continue

    return pids

def process_loop(stop_event, telemetry_logger, logger):
    while not stop_event.is_set():
        try:
            pids = get_process_list()

            # logger.debug(f"{len(pids)} процессов")
            logger.info(f"файл module_processes_monitoring.py: Логирование system_metrics - процессов найдено {len(pids)}")

            telemetry_logger.log_event("system_metrics", {
                "action": "process_list",
                "processes": [pid for pid, _ in pids]
            })

        except Exception as e:
            logger.error(f"process_loop error: {e}")

        time.sleep(PROCESS_INTERVAL)

def start_process_monitoring(stop_event, telemetry_logger, logger):
    logger.info("Запуск мониторинга system_metrics...")

    threading.Thread(target=cpu_memory_loop, args=(stop_event,telemetry_logger, logger), daemon=True).start()
    threading.Thread(target=process_loop, args=(stop_event,telemetry_logger, logger), daemon=True).start()
    threading.Thread(target=disk_loop, args=(stop_event,telemetry_logger, logger), daemon=True).start()
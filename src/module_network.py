from scapy.all import sniff, IP, TCP, UDP, DNS, get_if_list
from datetime import datetime
import threading
import queue

PACKET_QUEUE = queue.Queue(maxsize=5000)
PACKET_COUNTER = 0

def process_packet(pkt, logger):
    global PACKET_COUNTER
    PACKET_COUNTER += 1

    try:
        if IP not in pkt:
            return

        source = pkt[IP].src
        destination = pkt[IP].dst

        protocol = "IP"
        info = ""

        if TCP in pkt:
            protocol = "TCP"
            info = f"{pkt[TCP].sport}->{pkt[TCP].dport}"

        elif UDP in pkt:
            protocol = "UDP"
            info = f"{pkt[UDP].sport}->{pkt[UDP].dport}"

        elif DNS in pkt and pkt[DNS].qd:
            protocol = "DNS"
            info = pkt[DNS].qd.qname.decode(errors="ignore")

        PACKET_QUEUE.put_nowait({
            "packet_counter": PACKET_COUNTER,
            "source": source,
            "destination": destination,
            "protocol": protocol,
            "info": info,
            "length": len(pkt)
        })

    except queue.Full:
        logger.warning("файл module_network.py: Очередь пакетов переполнена. Некоторые пакеты будут потеряны.")

def packet_worker(stop_event, telemetry_logger,logger):
    while not stop_event.is_set():
        try:
            pkt = PACKET_QUEUE.get(timeout=0.5)

            telemetry_logger.log_event("network_metrics", pkt)

        except queue.Empty:
            logger.debug("файл module_network.py: Очередь пакетов пуста. Ожидание новых пакетов...")
            continue
        except Exception as e:
            logger.error(f"network worker error: {e}")

def sniff_loop(active_iface, stop_event, logger):
    while not stop_event.is_set():
        sniff(
            iface=active_iface,
            prn=lambda pkt: process_packet(pkt, logger),
            store=False,
            filter="ip",
            timeout=1
        )

def start_dump_network_traffic(stop_event, telemetry_logger, logger):
    logger.info("module_network.py: Старт сбора сетевой телеметрии...")

    lst = get_if_list()
    active_iface = None

    for i in lst:
        try:
            logger.debug(f"файл module_network.py: Проверка интерфейса {i}")

            sniff(
                iface=i,
                prn=lambda x: None,
                store=False,
                count=1,
                timeout=1
            )

            active_iface = i
            break

        except Exception:
            logger.error(f"файл module_network.py: Не удалось открыть интерфейс {i} для захвата пакетов")
            continue

    if not active_iface:
        logger.warning("файл module_network.py: Не найден активный сетевой интерфейс для захвата пакетов. Сетевая телеметрия не будет собираться.")
        return

    logger.info(f"файл module_network.py: Найден активный сетевой интерфейс для захвата пакетов: {active_iface}")

    threading.Thread(
        target=packet_worker,
        args=(stop_event, telemetry_logger, logger),
        daemon=True
    ).start()

    threading.Thread(
        target=sniff_loop,
        args=(active_iface, stop_event, logger),
        daemon=True
    ).start()
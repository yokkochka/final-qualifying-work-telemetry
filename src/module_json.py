import json
import os
from datetime import datetime, timedelta

class TelemetryLogger:
    def __init__(self, dirname=None):
        self.prefix_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if dirname is None:
            dirname = f"telemetry/telemetry_log_{self.prefix_time}"
        
        self.file_imitator_logs = f"{dirname}/imitator_logs_{self.prefix_time}.json"
        self.file_network_logs = f"{dirname}/network_metrics_{self.prefix_time}.json"
        self.file_user_activity_logs = f"{dirname}/user_activity_{self.prefix_time}.json"
        self.file_system_metrics_logs = f"{dirname}/system_metrics_{self.prefix_time}.json"

        self.final = f"{dirname}/final_telemetry_{self.prefix_time}.json" 

        self.dirname = dirname
        self._prepare_file()

    def _prepare_file(self):
        if not os.path.isdir('telemetry'):
            os.mkdir('telemetry')

        if not os.path.isdir(self.dirname):
            os.mkdir(self.dirname)

        if not os.path.exists(self.file_imitator_logs):
            with open(self.file_imitator_logs, "w", encoding="utf-8") as f:
                pass 
        if not os.path.exists(self.file_network_logs):
            with open(self.file_network_logs, "w", encoding="utf-8") as f:
                pass 

        if not os.path.exists(self.file_user_activity_logs):
            with open(self.file_user_activity_logs, "w", encoding="utf-8") as f:
                pass 

        if not os.path.exists(self.file_system_metrics_logs):
            with open(self.file_system_metrics_logs, "w", encoding="utf-8") as f:
                pass 
        if not os.path.exists(self.final):
            with open(self.final, "w", encoding="utf-8") as f:
                pass 

    def log_event(self, event_type, data):
        now = datetime.now()
        file_name = f"{self.dirname}/{event_type}_{self.prefix_time}.json"
        event = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S.%f"),  # ← добавили микросекунды
            "event_type": event_type,
            "data": data
        }


        with open(file_name, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_event_with_timestamp(self, event_type, data):
        date, time = data['timestamp'].split('T')
        del data['timestamp']
        file_name = f"{self.dirname}/{event_type}_{self.prefix_time}.json"
        event = {
            "date": date,
            "time": time,
            "event_type": event_type,
            "data": data
        }

        with open(file_name, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def sort_log_file(self):
        if not os.path.exists(self.final):
            return

        def parse_time(x):
            return datetime.strptime(
                f"{x['date']} {x['time']}".replace("T", " "),
                "%Y-%m-%d %H:%M:%S.%f"
            )

        events = []

        with open(self.file_network_logs, "r", encoding="utf-8") as f:
            events += [json.loads(line) for line in f if line.strip()]

        with open(self.file_user_activity_logs, "r", encoding="utf-8") as f:
            events += [json.loads(line) for line in f if line.strip()]

        with open(self.file_system_metrics_logs, "r", encoding="utf-8") as f:
            events += [json.loads(line) for line in f if line.strip()]

        with open(self.file_imitator_logs, "r", encoding="utf-8") as f:
            imitator_events = [json.loads(line) for line in f if line.strip()]

        if not events:
            return

        events.sort(key=parse_time)

        min_time = parse_time(events[0]) - timedelta(seconds=2)
        max_time = parse_time(events[-1]) + timedelta(seconds=2)

        filtered_imitator = [
            e for e in imitator_events
            if min_time <= parse_time(e) <= max_time
        ]

        events += filtered_imitator

        events.sort(key=parse_time)

        with open(self.final, "w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
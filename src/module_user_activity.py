import time
import threading

import psutil
import ctypes
import win32con
from pynput import keyboard, mouse
import win32gui
import win32process

PREV = {}

CURRENT_WINDOW = None
LAST_RECTS = {}
START_TIME = time.time()
DWMWA_CLOAKED = 14

def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd)

    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid).name()
    except:
        process = "unknown"
    return title, process

def on_key_press(key, telemetry_logger, logger):
    try:
        k = key.char
    except:
        k = str(key)

    title, process = get_active_window()

    logger.info(f"файл module_user_activity.py: Логирование события - key_press, клавиша: {k}, окно: {title}, процесс: {process}")
    telemetry_logger.log_event("user_activity", {
        "action": "key_press",
        "key": k,
        "window": title,
        "process": process
    })

def on_click(x, y, button, pressed, telemetry_logger, logger):
    if pressed:
        title, process = get_active_window()

        logger.info(f"файл module_user_activity.py: Логирование события - mouse_click, кнопка: {button}, позиция: ({x}, {y}), окно: {title}, процесс: {process}")
        telemetry_logger.log_event("user_activity", {
            "action": "mouse_click",
            "button": str(button),
            "position": (x, y),
            "window": title,
            "process": process
        })

def track_active_window(stop_event, telemetry_logger, logger):
    global CURRENT_WINDOW, START_TIME  

    while not stop_event.is_set():
        title, process = get_active_window()

        if CURRENT_WINDOW is None:
            CURRENT_WINDOW = (title, process)
            START_TIME = time.time()

        elif CURRENT_WINDOW != (title, process):
            duration = time.time() - START_TIME
    
            logger.info(f"файл module_user_activity.py: Логирование события - window_focus_duration, окно: {CURRENT_WINDOW[0]}, процесс: {CURRENT_WINDOW[1]}, длительность: {round(duration, 2)} сек")

            telemetry_logger.log_event("user_activity", {
                "action": "window_focus_duration",
                "window": CURRENT_WINDOW[0],
                "process": CURRENT_WINDOW[1],
                "duration_sec": round(duration, 2)
            })

            CURRENT_WINDOW = (title, process)
            START_TIME = time.time()

        time.sleep(1)

def is_cloaked(hwnd):
    cloaked = ctypes.c_int()
    try:
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_CLOAKED,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked)
        )
        return cloaked.value != 0
    except:
        return False

def is_taskbar_window(hwnd):
    if not win32gui.IsWindow(hwnd):
        return False

    if not win32gui.IsWindowVisible(hwnd):
        return False

    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
        return False

    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return False

    if is_cloaked(hwnd):
        return False

    title = win32gui.GetWindowText(hwnd)
    if not title.strip():
        return False

    return True

def get_process_name(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name()
    except:
        return "unknown"
    
def get_taskbar_windows():
    result = {}

    def enum_handler(hwnd, _):
        if is_taskbar_window(hwnd):
            title = win32gui.GetWindowText(hwnd)
            process = get_process_name(hwnd)

            result[hwnd] = {
                "title": title,
                "process": process
            }

    win32gui.EnumWindows(enum_handler, None)
    return result

def window_open_close_loop(stop_event, telemetry_logger, logger):
    global PREV, missing_since

    
    PREV = get_taskbar_windows()
    logger.info(f"файл module_user_activity.py: Инициализация окна - получено {len(PREV)} окон {[win32gui.GetWindowText(hwnd) for hwnd in PREV]} в начальном снепшоте")
    

    while not stop_event.is_set():
        current = get_taskbar_windows()
        for hwnd, meta in current.items():
            if hwnd not in PREV:
                logger.info(f"файл module_user_activity.py: Логирование события - window_open, окно: {meta['title']} СЕЙЧАС не было найдено в ПРЕДЫДУЩИХ ОКНАХ")
                telemetry_logger.log_event("user_activity", {
                    "action": "window_open",
                    "process": meta["process"],
                    "title": meta["title"]
                })

        for hwnd, meta in PREV.items():
            if hwnd not in current:
                logger.info(f"файл module_user_activity.py: Окно {meta['title']} отсутствует в ТЕКУЩЕМ снепшоте (было закрыто)")
                telemetry_logger.log_event("user_activity", {
                    "action": "window_close",
                    "process": meta["process"],
                    "title": meta["title"]
                })
        PREV = current

        time.sleep(0.2)

def move_and_resize(stop_event, telemetry_logger, logger):
    global LAST_RECTS

    LAST_RECTS = {}
    while not stop_event.is_set():
        current = get_taskbar_windows()

        for hwnd, meta in current.items():
            try:
                rect = win32gui.GetWindowRect(hwnd)
                left, top, right, bottom = rect

                width = right - left
                height = bottom - top

                if hwnd not in LAST_RECTS:
                    LAST_RECTS[hwnd] = (left, top, width, height)
                    continue

                prev_left, prev_top, prev_w, prev_h = LAST_RECTS[hwnd]

                moved = (prev_left != left or prev_top != top)
                resized = (prev_w != width or prev_h != height)

                if moved or resized:
                    event_type = []

                    if resized:
                        event_type.append("resize")
                    elif moved:
                        event_type.append("move")
                    

                    logger.info(
                        f"файл module_user_activity.py: Логирование события - window_{'_'.join(event_type)}, "
                        f"окно: {meta['title']}, процесс: {meta['process']}, "
                        f"позиция: ({left}, {top}), размер: ({width}x{height})"
                    )

                    telemetry_logger.log_event("user_activity", {
                        "action": "window_" + "_".join(event_type),
                        "process": meta["process"],
                        "title": meta["title"],
                        "position": [left, top],
                        "size": [width, height]
                    })

                LAST_RECTS[hwnd] = (left, top, width, height)

            except:
                continue

        time.sleep(0.2)

def start_user_telemetry(stop_event, telemetry_logger, logger):
    keyboard_listener = keyboard.Listener(on_press=lambda key: on_key_press(key, telemetry_logger, logger))
    mouse_listener = mouse.Listener(on_click=lambda x, y, button, pressed: on_click(x, y, button, pressed, telemetry_logger, logger))

    keyboard_listener.start()
    logger.info(f"файл module_user_activity.py: Клавиатурный слушатель запущен")
    mouse_listener.start()
    logger.info(f"файл module_user_activity.py: Слушатель мыши запущен")

    threading.Thread(target=track_active_window, args=(stop_event,telemetry_logger, logger), daemon=True).start()
    threading.Thread(target=window_open_close_loop, args=(stop_event,telemetry_logger, logger), daemon=True).start()
    threading.Thread(target=move_and_resize, args=(stop_event,telemetry_logger, logger), daemon=True).start()

    logger.info(f"файл module_user_activity.py: Сбор телеметрии пользовательской активности запущен...")
    keyboard_listener.join()
    mouse_listener.join()





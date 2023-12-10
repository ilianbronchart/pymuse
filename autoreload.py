import subprocess
import time
import threading
from multiprocessing.connection import Client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.config import IPC_CONN

class ReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_called = 0
        self.debounce_seconds = 0.5  # Time interval in seconds

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            current_time = time.time()
            if current_time - self.last_called > self.debounce_seconds:
                print("Python file change detected. Restarting process.")
                kill_process()
                start_process()
                self.last_called = current_time

def start_process():
    global process
    process = subprocess.Popen('python .\main.py', shell=True)
    monitor_process_thread = threading.Thread(target=monitor_process, args=(process,))
    monitor_process_thread.start()

def kill_process():
    global process
    if process:
        try:
            conn = Client(IPC_CONN)
            conn.send('close')
            conn.close()
            process.wait()
        except Exception as e:
            print("Error while killing process:", e)

def monitor_process(proc):
    proc.wait()
    stop_script_event.set()  # Set the event to signal the main script to end

process = None
stop_script_event = threading.Event()  # Event to signal when to stop the main script
start_process()

# Create an observer
observer = Observer()
observer.schedule(ReloadHandler(), path='.', recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    kill_process()  # Ensure the process is killed on script exit
observer.join()

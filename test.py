# import threading

# def list_threads():
#     # Get all active threads
#     all_threads = threading.enumerate()
    
#     # Print information about each thread
#     print(f"Total Threads: {len(all_threads)}")
#     for i, thread in enumerate(all_threads):
#         print(f"Thread {i+1}: Name = {thread.name}, ID = {thread.ident}")

# if __name__ == "__main__":
#     def dummy_function():
#         while True:
#             pass

#     # Start some dummy threads
#     for i in range(5):
#         t = threading.Thread(target=dummy_function)
#         t.start()

#     # List all threads
#     list_threads()

# import psutil
# import os
import sys
# import time

# def get_cpu_usage_for_process(pid):
#     try:
#         proc = psutil.Process(pid)
#         cpu_usage = proc.cpu_percent() 
#         cpu_usage = psutil.cpu_percent()
#         # print(proc.__dict__)     
#         print(cpu_usage)     
#         return cpu_usage
#     except psutil.NoSuchProcess:
#         print(f"No such process with PID {pid}")
#         return None

# if __name__ == "__main__":
#     # Get the current process ID
#     current_pid = os.getpid()
    
#     # Get the total CPU usage for the current process
#     c=0
#     while c<=1000000:
#         c+=1
#         total_cpu_usage = get_cpu_usage_for_process(current_pid)
#         # total_cpu_usage = 0
#         if total_cpu_usage is None:
#             print(f"None None None {current_pid}")
#         message = f"{c} Total CPU usage for process {current_pid}: {total_cpu_usage}%"
#         # sys.stdout.write("\r" + message)
#         print(message)
#         sys.stdout.flush()
    
#     print("\nDone.")
import threading
import psutil
import os
import sys

import subprocess

def get_thread_usage_via_cli(pid):
    try:
        # Insert relevant system commands to profile CPU - can adjust based on need
        # Example: using 'ps' to view threads, though not perfect for CPU monitoring
        result = subprocess.run(['ps', '-M', str(pid)], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")


def get_cpu_usage_for_process(pid, counter):
    try:
        proc = psutil.Process(pid)
        
        # Get the CPU usage over an interval to ensure it's up to date
        proc.cpu_percent(interval=0.1)  
        
        while counter[0] <= 10000000:
            # CPU usage of the process
            cpu_usage = proc.cpu_percent(interval=None)

            # Get overall CPU usage
            overall_cpu_usage = psutil.cpu_percent(interval=None)
            get_thread_usage_via_cli(pid)

            message = f"{counter[0]} Total CPU usage for process {pid}: {cpu_usage}% across all threads"
            sys.stdout.write("\r" + message)
            sys.stdout.flush()

            # Increment counter
            counter[0] += 1

    except psutil.NoSuchProcess:
        print(f"No such process with PID {pid}")
        return None

def thread_worker(counter):
    current_pid = os.getpid()
    get_cpu_usage_for_process(current_pid, counter)

if __name__ == "__main__":
    # Share a counter among threads using a list for quick mutable access
    shared_counter = [1]

    threads = []
    for i in range(5):  # Number of threads
        t = threading.Thread(target=thread_worker, args=(shared_counter,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\nDone.")
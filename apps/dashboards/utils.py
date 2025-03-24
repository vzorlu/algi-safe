import psutil
import GPUtil

def get_device_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent

    gpus = GPUtil.getGPUs()
    if gpus:
        gpu_usage = gpus[0].load * 100
    else:
        gpu_usage = None

    return cpu_usage, gpu_usage, ram_usage


#

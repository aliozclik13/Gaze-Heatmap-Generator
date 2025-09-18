from __future__ import annotations

def read_gpu_snapshot():
    """
    NVML (pynvml) veya GPUtil mevcutsa temel GPU ölçüleri döndürür.
    Yoksa None döner. Tek-GPU odaklı basit bir okuma yapar.
    """
    # Öncelik: pynvml
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(h)
        mem = pynvml.nvmlDeviceGetMemoryInfo(h)
        temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
        try:
            power = pynvml.nvmlDeviceGetPowerUsage(h) / 1000.0  # mW -> W
        except Exception:
            power = None
        out = {
            "util_percent": float(util.gpu),
            "mem_used_mb": float(mem.used)/(1024*1024),
            "mem_total_mb": float(mem.total)/(1024*1024),
            "temp_c": float(temp),
            "power_w": power
        }
        pynvml.nvmlShutdown()
        return out
    except Exception:
        pass

    # Yedek: GPUtil
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if not gpus:
            return None
        g = gpus[0]
        return {
            "util_percent": float(g.load*100.0),
            "mem_used_mb": float(g.memoryUsed),
            "mem_total_mb": float(g.memoryTotal),
            "temp_c": float(g.temperature),
            "power_w": None  # GPUtil tipik olarak güç vermez
        }
    except Exception:
        pass

    return None
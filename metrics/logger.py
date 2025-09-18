from __future__ import annotations
import os, csv, json, time, threading, queue, statistics, tracemalloc
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import psutil

try:
    from .gpu import read_gpu_snapshot
except Exception:
    def read_gpu_snapshot():
        # GPU yoksa veya kütüphane kurulmamışsa None döner
        return None


@dataclass
class Sample:
    ts: float                      # epoch seconds
    uptime_s: float                # oturum başlangıcından itibaren süre
    # Process-level (Python proc)
    proc_cpu_percent: float
    proc_mem_rss_mb: float
    proc_mem_vms_mb: float
    proc_mem_pct: float
    open_fds: Optional[int]
    # System-level
    sys_cpu_percent: float
    sys_ram_used_mb: float
    sys_ram_available_mb: float
    sys_ram_percent: float
    sys_swap_used_mb: float
    sys_swap_percent: float
    # IO / NET (system cumulative; derive rates offline if needed)
    disk_read_mb: float
    disk_write_mb: float
    net_bytes_sent_mb: float
    net_bytes_recv_mb: float
    # Python-level
    py_tracemalloc_current_mb: Optional[float]
    py_tracemalloc_peak_mb: Optional[float]
    # GPU (optional; None if unavailable)
    gpu_util_percent: Optional[float]
    gpu_mem_used_mb: Optional[float]
    gpu_mem_total_mb: Optional[float]
    gpu_temp_c: Optional[float]
    gpu_power_w: Optional[float]
    # Request-scoped (en son kaydedilen istek süresi)
    last_request_ms: Optional[float]


class MetricsSession:
    """
    Tek (pid, test_id) çifti için sürekli örnekleme yapan oturum.
    """
    def __init__(self, pid: str, test_id: int, data_dir: str, interval_s: float = 1.0):
        self.pid = pid
        self.test_id = int(test_id)
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.interval_s = interval_s
        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._started_at = time.perf_counter()
        self._proc = psutil.Process(os.getpid())
        self._csv_path = os.path.join(
            self.data_dir, f"metrics_{self.pid}_test{self.test_id}.csv"
        )
        self._json_summary_path = os.path.join(
            self.data_dir, f"metrics_{self.pid}_test{self.test_id}_summary.json"
        )
        self._csv_file = None
        self._csv_writer = None
        self._samples_count = 0
        self._req_time_ms_q: "queue.Queue[float]" = queue.Queue()
        self._last_request_ms: Optional[float] = None

        # Disk/NET counters (system cumulative)
        self._disk0 = psutil.disk_io_counters()
        self._net0 = psutil.net_io_counters()

        # Pre-warm CPU percent
        self._proc.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None)

        # Python tracemalloc
        try:
            tracemalloc.start()
            self._use_tracemalloc = True
        except Exception:
            self._use_tracemalloc = False

        self._init_csv()

    def _init_csv(self):
        is_new = not os.path.exists(self._csv_path)
        self._csv_file = open(self._csv_path, "a", newline="", encoding="utf-8")
        self._csv_writer = csv.writer(self._csv_file)
        if is_new:
            self._csv_writer.writerow([
                "ts","uptime_s",
                "proc_cpu_percent","proc_mem_rss_mb","proc_mem_vms_mb","proc_mem_pct","open_fds",
                "sys_cpu_percent","sys_ram_used_mb","sys_ram_available_mb","sys_ram_percent","sys_swap_used_mb","sys_swap_percent",
                "disk_read_mb","disk_write_mb","net_bytes_sent_mb","net_bytes_recv_mb",
                "py_tracemalloc_current_mb","py_tracemalloc_peak_mb",
                "gpu_util_percent","gpu_mem_used_mb","gpu_mem_total_mb","gpu_temp_c","gpu_power_w",
                "last_request_ms"
            ])

    def note_request_ms(self, elapsed_ms: float):
        try:
            self._req_time_ms_q.put_nowait(float(elapsed_ms))
        except queue.Full:
            pass

    def _collect(self) -> Sample:
        now = time.time()
        uptime = time.perf_counter() - self._started_at

        # Process
        proc_cpu = self._proc.cpu_percent(interval=None)
        mem = self._proc.memory_info()
        try:
            mem_pct = self._proc.memory_percent()
        except Exception:
            mem_pct = 0.0
        try:
            open_fds = self._proc.num_fds() if hasattr(self._proc, "num_fds") else None
        except Exception:
            open_fds = None

        # System
        sys_cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # IO/NET (cumulative since boot)
        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()

        disk_read_mb = (disk.read_bytes - self._disk0.read_bytes) / (1024*1024)
        disk_write_mb = (disk.write_bytes - self._disk0.write_bytes) / (1024*1024)
        net_sent_mb = (net.bytes_sent - self._net0.bytes_sent) / (1024*1024)
        net_recv_mb = (net.bytes_recv - self._net0.bytes_recv) / (1024*1024)

        # Python tracemalloc
        if self._use_tracemalloc:
            cur, peak = tracemalloc.get_traced_memory()
            cur_mb = cur / (1024*1024)
            peak_mb = peak / (1024*1024)
        else:
            cur_mb = peak_mb = None

        # GPU (optional)
        gpu = read_gpu_snapshot()
        if gpu:
            gpu_util = gpu.get("util_percent")
            gpu_mem_used = gpu.get("mem_used_mb")
            gpu_mem_total = gpu.get("mem_total_mb")
            gpu_temp_c = gpu.get("temp_c")
            gpu_power_w = gpu.get("power_w")
        else:
            gpu_util = gpu_mem_used = gpu_mem_total = gpu_temp_c = gpu_power_w = None

        # Son istek süresi
        try:
            while True:
                self._last_request_ms = self._req_time_ms_q.get_nowait()
        except queue.Empty:
            pass

        return Sample(
            ts=now,
            uptime_s=uptime,
            proc_cpu_percent=proc_cpu,
            proc_mem_rss_mb=mem.rss/(1024*1024),
            proc_mem_vms_mb=mem.vms/(1024*1024),
            proc_mem_pct=mem_pct,
            open_fds=open_fds,
            sys_cpu_percent=sys_cpu,
            sys_ram_used_mb=(vm.used/(1024*1024)),
            sys_ram_available_mb=(vm.available/(1024*1024)),
            sys_ram_percent=vm.percent,
            sys_swap_used_mb=(swap.used/(1024*1024)),
            sys_swap_percent=swap.percent,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb,
            net_bytes_sent_mb=net_sent_mb,
            net_bytes_recv_mb=net_recv_mb,
            py_tracemalloc_current_mb=cur_mb,
            py_tracemalloc_peak_mb=peak_mb,
            gpu_util_percent=gpu_util,
            gpu_mem_used_mb=gpu_mem_used,
            gpu_mem_total_mb=gpu_mem_total,
            gpu_temp_c=gpu_temp_c,
            gpu_power_w=gpu_power_w,
            last_request_ms=self._last_request_ms
        )

    def _write(self, s: Sample):
        self._csv_writer.writerow([
            s.ts, s.uptime_s,
            s.proc_cpu_percent, s.proc_mem_rss_mb, s.proc_mem_vms_mb, s.proc_mem_pct, s.open_fds,
            s.sys_cpu_percent, s.sys_ram_used_mb, s.sys_ram_available_mb, s.sys_ram_percent, s.sys_swap_used_mb, s.sys_swap_percent,
            s.disk_read_mb, s.disk_write_mb, s.net_bytes_sent_mb, s.net_bytes_recv_mb,
            s.py_tracemalloc_current_mb, s.py_tracemalloc_peak_mb,
            s.gpu_util_percent, s.gpu_mem_used_mb, s.gpu_mem_total_mb, s.gpu_temp_c, s.gpu_power_w,
            s.last_request_ms
        ])
        self._csv_file.flush()
        self._samples_count += 1

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._loop, name=f"metrics-{self.pid}-{self.test_id}", daemon=True)
        self._thread.start()

    def _loop(self):
        while not self._stop_evt.is_set():
            s = self._collect()
            self._write(s)
            self._stop_evt.wait(self.interval_s)

    def stop(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._finalize()

    def _finalize(self):
        try:
            self._csv_file.flush()
            self._csv_file.close()
        except Exception:
            pass

        try:
            rows = []
            with open(self._csv_path, "r", encoding="utf-8") as f:
                r = csv.DictReader(f)
                for row in r:
                    rows.append(row)

            def numcol(col):
                vals = []
                for row in rows:
                    v = row.get(col)
                    if v in (None, "", "None"):
                        continue
                    try:
                        vals.append(float(v))
                    except:
                        pass
                return vals

            keys = [
                "proc_cpu_percent","proc_mem_rss_mb","sys_cpu_percent",
                "sys_ram_percent","py_tracemalloc_current_mb","gpu_util_percent",
                "last_request_ms"
            ]
            summary: Dict[str, Any] = {
                "pid": self.pid,
                "test_id": self.test_id,
                "samples": len(rows),
                "duration_s": float(rows[-1]["uptime_s"]) if rows else 0.0,
            }
            for k in keys:
                vals = numcol(k)
                if vals:
                    summary[k] = {
                        "min": min(vals),
                        "max": max(vals),
                        "mean": statistics.fmean(vals),
                        "p50": statistics.median(vals),
                    }
                else:
                    summary[k] = None

            with open(self._json_summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class MetricsManager:
    """
    Birden çok (pid, test_id) oturumunu iş parçacıkları ile yönetir.
    """
    def __init__(self, data_dir: str, interval_s: float = 1.0):
        self.data_dir = data_dir
        self.interval_s = interval_s
        self._lock = threading.Lock()
        self._sessions: Dict[tuple[str,int], MetricsSession] = {}

    def key(self, pid: str, test_id: int):
        return (pid, int(test_id))

    def ensure_started(self, pid: str, test_id: int):
        k = self.key(pid, test_id)
        with self._lock:
            sess = self._sessions.get(k)
            if not sess:
                sess = MetricsSession(pid, test_id, self.data_dir, self.interval_s)
                self._sessions[k] = sess
                sess.start()
            return sess

    def note_request_ms(self, pid: str, test_id: int, elapsed_ms: float):
        k = self.key(pid, test_id)
        with self._lock:
            sess = self._sessions.get(k)
            if sess:
                sess.note_request_ms(elapsed_ms)

    def stop(self, pid: str, test_id: int):
        k = self.key(pid, test_id)
        with self._lock:
            sess = self._sessions.pop(k, None)
        if sess:
            sess.stop()
            return True
        return False

    def stop_all(self):
        with self._lock:
            keys = list(self._sessions.keys())
        for pid, test_id in keys:
            self.stop(pid, test_id)

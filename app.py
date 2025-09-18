from flask import Flask, request, render_template, url_for, jsonify
import csv, os, re, glob, time
import json

from metrics.logger import MetricsManager  # <<< EKLENDİ

app = Flask(__name__, static_url_path="/static", template_folder="templates")


DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TEST_RE = re.compile(r"^gaze_(?P<pid>.+?)_test(?P<n>\d+)\.csv$")

# --- METRICS ---
metrics = MetricsManager(data_dir=DATA_DIR, interval_s=1.0)  # 1 Hz örnekleme
# ---------------

def next_test_pid_for(pid: str) -> int:
    files = glob.glob(os.path.join(DATA_DIR, f"gaze_{pid}_test*.csv"))
    if not files:
        return 1
    maxn = 0
    for f in files:
        m = TEST_RE.match(os.path.basename(f))
        if m:
            try:
                n = int(m.group("n"))
                if n > maxn:
                    maxn = n
            except:
                pass
    return maxn + 1

@app.before_request
def _tic():
    # İstek bazlı süre ölçümü (ms)
    request._tic = time.perf_counter()

@app.after_request
def _toc(resp):
    try:
        start = getattr(request, "_tic", None)
        if start is not None:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            # İstekten pid/test_id çıkarıp mevcut oturuma yaz
            pid = None
            test_id = None

            # 1) JSON body
            if request.is_json:
                try:
                    data = request.get_json(silent=True) or {}
                    pid = (data.get("pid") or "").strip() or None
                    test_id = int(data.get("test_id")) if data.get("test_id") is not None else None
                except Exception:
                    pass

            # 2) Query string (örn: GET /?pid=...&test_id=...)
            if pid is None:
                pid = (request.args.get("pid") or "").strip() or None
            if test_id is None:
                try:
                    test_id = int(request.args.get("test_id")) if request.args.get("test_id") else None
                except Exception:
                    test_id = None

            if pid and test_id:
                metrics.note_request_ms(pid, test_id, elapsed_ms)
    except Exception:
        pass
    return resp

@app.route("/")
def index():
    pid = request.args.get("pid", "participant").strip() or "participant"
    test_id = next_test_pid_for(pid)
    return render_template("index.html", pid=pid, test_id=test_id)

@app.route("/save_gaze", methods=["POST"])
def save_gaze():
    """
    Beklenen JSON:
      { pid, test_id, frame, x, y, vw, vh }
    """
    data = request.get_json(force=True) or {}
    pid = (data.get("pid") or "participant").strip() or "participant"
    try:
        test_id = int(data.get("test_id") or 1)
    except:
        test_id = 1

    # --- METRICS: bu oturum için ölçümü başlat (idempotent) ---
    metrics.ensure_started(pid, test_id)

    path = os.path.join(DATA_DIR, f"gaze_{pid}_test{test_id}.csv")
    is_new = not os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["frame", "x", "y", "vw", "vh"])  # artık frame kullanıyoruz
        w.writerow([
            data.get("frame", "NA"),
            data.get("x", "NA"),
            data.get("y", "NA"),
            data.get("vw", "NA"),
            data.get("vh", "NA"),
        ])
    return ("", 204)

@app.route("/end_test", methods=["POST"])
def end_test():
    """
    Testi bitirir, ölçüm iş parçacığını durdurur ve özet JSON dosyasını oluşturur.
    Beklenen JSON: { pid, test_id }
    """
    data = request.get_json(force=True) or {}
    pid = (data.get("pid") or "").strip()
    test_id = data.get("test_id")

    if not pid or test_id is None:
        return jsonify({"error": "pid ve test_id gerekli"}), 400

    try:
        test_id = int(test_id)
    except Exception:
        return jsonify({"error": "test_id tam sayı olmalı"}), 400

    stopped = metrics.stop(pid, test_id)
    if not stopped:
        return jsonify({"status": "no_active_session"}), 200

    # Özet dosyanın yolu (logger içinde sabit)
    summary_path = os.path.join(DATA_DIR, f"metrics_{pid}_test{test_id}_summary.json")
    out = {"status": "stopped", "summary_json": summary_path}
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            out["summary"] = json.load(f)
    except Exception:
        pass
    return jsonify(out), 200

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # WebGazer kamera erişimi için HTTPS tavsiye edilir; yerelde çalıştırıyorsan
    # Chrome'da "localhost" güvenilir kabul edilir.
    try:
        app.run(host="127.0.0.1", port=5000, debug=True)
    finally:
        # Uygulama kapanırken tüm oturumları temiz kapat
        metrics.stop_all()
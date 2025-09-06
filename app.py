from flask import Flask, request, render_template, url_for
import csv, os, re, glob

app = Flask(__name__, static_url_path="/static", template_folder="templates")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TEST_RE = re.compile(r"^gaze_(?P<pid>.+?)_test(?P<n>\d+)\.csv$")

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

@app.route("/")
def index():
    pid = request.args.get("pid", "participant").strip() or "participant"
    test_id = next_test_pid_for(pid)
    return render_template("index.html", pid=pid, test_id=test_id)

@app.route("/save_gaze", methods=["POST"])
def save_gaze():
    """
    Beklenen JSON:
      { pid, test_id, time, x, y, vw, vh }
    """
    data = request.get_json(force=True) or {}
    pid = (data.get("pid") or "participant").strip() or "participant"
    try:
        test_id = int(data.get("test_id") or 1)
    except:
        test_id = 1

    path = os.path.join(DATA_DIR, f"gaze_{pid}_test{test_id}.csv")
    is_new = not os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["time", "x", "y", "vw", "vh"])
        w.writerow([
            data.get("time", "NA"),
            data.get("x", "NA"),
            data.get("y", "NA"),
            data.get("vw", "NA"),
            data.get("vh", "NA"),
        ])
    return ("", 204)

if __name__ == "__main__":
    # WebGazer kamera erişimi için HTTPS tavsiye edilir; yerelde çalıştırıyorsan
    # Chrome'da "localhost" güvenilir kabul edilir.
    app.run(host="127.0.0.1", port=5000, debug=True)

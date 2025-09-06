import pandas as pd
import cv2
import numpy as np
import os
import glob
import re
from tqdm import tqdm # İlerleme çubuğu için (pip install tqdm)

# --- AYARLAR ---
DATA_DIR = "data"
VIDEO_PATH = os.path.join("static", "video.mp4")
OUTPUT_DIR = "results"

# Heatmap Ayarları
GAUSSIAN_BLUR_KERNEL_SIZE = (21, 21)
GAUSSIAN_BLUR_SIGMA = 50
HEATMAP_ALPHA = 0.4
COLOR_MAP = cv2.COLORMAP_JET

# app.py'dan alınan dosya adı regex'i
TEST_RE = re.compile(r"^gaze_(?P<pid>.+?)_test(?P<n>\d+)\.csv$")

def find_unique_tests(data_dir):
    """
    Veri klasöründeki tüm .csv dosyalarını tarar ve benzersiz test
    numaralarının bir listesini döndürür (örn: [1, 2, 3]).
    """
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    test_ids = set()
    for f in csv_files:
        match = TEST_RE.match(os.path.basename(f))
        if match:
            test_ids.add(int(match.group("n")))
    
    if not test_ids:
        print(f"Uyarı: '{data_dir}' klasöründe geçerli formatta (gaze_pid_testN.csv) dosya bulunamadı.")
        return []
        
    return sorted(list(test_ids))

def load_gaze_data_for_test(data_dir, test_id):
    """
    Belirli bir test numarasına ait tüm .csv dosyalarını yükler ve birleştirir.
    """
    # Sadece ilgili test dosyalarını seçmek için glob deseni
    file_pattern = os.path.join(data_dir, f"*_test{test_id}.csv")
    csv_files = glob.glob(file_pattern)
    
    if not csv_files:
        print(f"Hata: Test #{test_id} için hiç .csv dosyası bulunamadı.")
        return None
    
    all_dataframes = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            if all(col in df.columns for col in ['time', 'x', 'y', 'vw', 'vh']):
                all_dataframes.append(df)
            else:
                print(f"Uyarı: '{f}' dosyasında gerekli sütunlar eksik, atlanıyor.")
        except Exception as e:
            print(f"Uyarı: '{f}' dosyası okunurken hata oluştu: {e}, atlanıyor.")

    if not all_dataframes:
        print(f"Hata: Test #{test_id} için hiç geçerli gaze verisi yüklenemedi.")
        return None

    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df.sort_values(by='time', inplace=True)
    print(f"Test #{test_id} için {len(csv_files)} dosyadan toplam {len(combined_df)} bakış noktası yüklendi.")
    return combined_df

def create_heatmap(points, width, height):
    """Verilen noktalardan bir heatmap oluşturur."""
    heatmap = np.zeros((height, width), dtype=np.float32)
    for _, row in points.iterrows():
        x, y = int(row['x']), int(row['y'])
        if 0 <= x < width and 0 <= y < height:
            heatmap[y, x] += 1
    return heatmap

def process_video_for_test(gaze_df, test_id):
    """
    Belirli bir testin gaze verilerini kullanarak heatmap videosu oluşturur.
    """
    output_video_path = os.path.join(OUTPUT_DIR, f"heatmap_video_test{test_id}.mp4")
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Hata: '{VIDEO_PATH}' videosu açılamadı.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # DÜZELTME: tqdm() çağrısı artık doğru çalışacak
    for frame_idx in tqdm(range(total_frames), desc=f"İşleniyor: Test #{test_id}"):
        ret, frame = cap.read()
        if not ret:
            break

        current_time = frame_idx / fps
        time_window = 0.5
        points_in_frame = gaze_df[
            (gaze_df['time'] >= current_time - (time_window / 2)) & 
            (gaze_df['time'] < current_time + (time_window / 2))
        ]

        if not points_in_frame.empty:
            heatmap_raw = create_heatmap(points_in_frame, width, height)
            heatmap_blurred = cv2.GaussianBlur(heatmap_raw, GAUSSIAN_BLUR_KERNEL_SIZE, GAUSSIAN_BLUR_SIGMA)
            heatmap_normalized = cv2.normalize(heatmap_blurred, None, 0, 255, cv2.NORM_MINMAX)
            heatmap_colored = cv2.applyColorMap(heatmap_normalized.astype(np.uint8), COLOR_MAP)
            overlayed_frame = cv2.addWeighted(frame, 1 - HEATMAP_ALPHA, heatmap_colored, HEATMAP_ALPHA, 0)
            out.write(overlayed_frame)
        else:
            out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"✓ Test #{test_id} için video başarıyla '{output_video_path}' konumuna kaydedildi.")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Klasördeki tüm benzersiz test numaralarını bul
    test_ids_to_process = find_unique_tests(DATA_DIR)
    
    if not test_ids_to_process:
        return

    print(f"Bulunan Testler: {test_ids_to_process}")
    print("-" * 30)

    # 2. Her bir test için döngü başlat
    for test_id in test_ids_to_process:
        # O teste ait verileri yükle
        gaze_df = load_gaze_data_for_test(DATA_DIR, test_id)
        if gaze_df is not None:
            # Videoyu işle
            process_video_for_test(gaze_df, test_id)
            print("-" * 30)

if __name__ == "__main__":
    try:
        # DÜZELTME: Buradaki importlar sadece kontrol amaçlı,
        # 'tqdm' zaten yukarıda doğru şekilde import edildiği için buradan kaldırıldı.
        import pandas, cv2, numpy
    except ImportError as e:
        print(f"Hata: Gerekli bir kütüphane eksik: {e.name}")
        print(f"Lütfen 'pip install pandas opencv-python numpy tqdm' komutunu çalıştırarak yükleyin.")
    else:
        main()

import cv2
import os
import subprocess
from tqdm import tqdm
import re
import json

def extract_frames(video_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for f in os.listdir(output_folder):
        os.remove(os.path.join(output_folder, f))
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        os.path.join(output_folder, "frame_%05d.png")
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def extract_audio(video_path, output_audio):
    if os.path.exists(output_audio):
        os.remove(output_audio)  # supprime si déjà existant

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn",
        "-acodec", "copy",
        output_audio
    ]
    print(f"Extraction audio de : {video_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur ffmpeg extraction audio :\n{result.stderr}")
        return False
    if not os.path.exists(output_audio):
        print("⚠️ Le fichier audio n'a pas été créé.")
        return False
    print(f"Audio extrait : {output_audio}")
    return True

def rebuild_video_with_audio(frames_folder, audio_file, output_video, fps=25):
    print(f"Reconstruction vidéo MP4 avec audio : {output_video}")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-start_number", "1",
        "-i", os.path.join(frames_folder, "frame_%05d.png"),
        "-i", audio_file,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",    # important pour couper la vidéo à la durée la plus courte entre vidéo et audio
        "-pix_fmt", "yuv420p",
        output_video
    ]
    subprocess.run(cmd)

def find_matching_sd(video_hd_name, list_sd_files):
    pattern = re.compile(r"[0-9A-Z]{16}")
    match = pattern.search(video_hd_name)
    if not match:
        return None
    code_unique = match.group(0)
    for sd_file in list_sd_files:
        if code_unique in sd_file:
            return sd_file
    return None

def select_roi_from_first_video(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError(f"Impossible de lire la vidéo {video_path}")

    print(f"Sélectionnez la zone du filigrane dans la fenêtre (clic-glisser + Entrée) pour la vidéo : {video_path}")
    roi = cv2.selectROI("Zone filigrane (HD)", frame, False, False)
    cv2.destroyAllWindows()
    return roi, frame.shape[:2]

def clear_folder(folder):
    if os.path.exists(folder):
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
    else:
        os.makedirs(folder)

def get_video_duration(video_path):
    """Retourne la durée en secondes de la vidéo avec ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    info = json.loads(result.stdout)
    duration = float(info["format"]["duration"])
    return duration

def main():
    folder_hd = input("Chemin dossier vidéos HD : ").strip()
    folder_sd = input("Chemin dossier vidéos SD : ").strip()
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)

    hd_files = sorted([f for f in os.listdir(folder_hd) if f.lower().endswith(('.mp4', '.mov', '.avi'))])
    sd_files = sorted([f for f in os.listdir(folder_sd) if f.lower().endswith(('.mp4', '.mov', '.avi'))])

    if not hd_files or not sd_files:
        print("Aucune vidéo trouvée dans un des dossiers.")
        return

    roi, (h_hd_frame, w_hd_frame) = select_roi_from_first_video(os.path.join(folder_hd, hd_files[0]))
    x_hd, y_hd, w_hd, h_hd = roi

    sd_match = find_matching_sd(hd_files[0], sd_files)
    if not sd_match:
        print(f"Pas de correspondance SD pour {hd_files[0]}")
        return
    cap_sd = cv2.VideoCapture(os.path.join(folder_sd, sd_match))
    ret, frame_sd = cap_sd.read()
    cap_sd.release()
    if not ret:
        print(f"Impossible de lire la vidéo SD {sd_match}")
        return
    h_sd_frame, w_sd_frame = frame_sd.shape[:2]

    scale_x = w_sd_frame / w_hd_frame
    scale_y = h_sd_frame / h_hd_frame

    x_sd = int(x_hd * scale_x)
    y_sd = int(y_hd * scale_y)
    w_sd_roi = int(w_hd * scale_x)
    h_sd_roi = int(h_hd * scale_y)

    print(f"Zone filigrane HD : {(x_hd, y_hd, w_hd, h_hd)}")
    print(f"Zone filigrane SD adaptée : {(x_sd, y_sd, w_sd_roi, h_sd_roi)}")

    for hd_file in hd_files:
        print(f"\nTraitement de {hd_file}...")

        sd_file = find_matching_sd(hd_file, sd_files)
        if not sd_file:
            print(f"⚠️ Pas de vidéo SD correspondante pour {hd_file}, skip.")
            continue

        path_hd = os.path.join(folder_hd, hd_file)
        path_sd = os.path.join(folder_sd, sd_file)

        frames_hd_dir = "frames_hd_temp"
        frames_sd_dir = "frames_sd_temp"
        frames_out_dir = "frames_out_temp"
        audio_file = "audio_sd.aac"

        for d in [frames_hd_dir, frames_sd_dir, frames_out_dir]:
            clear_folder(d)

        print("  Extraction frames HD...")
        extract_frames(path_hd, frames_hd_dir)
        print("  Extraction frames SD...")
        extract_frames(path_sd, frames_sd_dir)

        print("  Extraction audio SD...")
        extract_audio(path_hd, audio_file)

        frames_hd = sorted(os.listdir(frames_hd_dir))
        frames_sd = sorted(os.listdir(frames_sd_dir))

        min_len = min(len(frames_hd), len(frames_sd))

        cap_hd = cv2.VideoCapture(path_hd)
        fps = cap_hd.get(cv2.CAP_PROP_FPS)
        cap_hd.release()
        if fps <= 0:
            fps = 25

        duration_sd = get_video_duration(path_sd)
        if duration_sd is None:
            print(f"Impossible de récupérer la durée de la vidéo SD {sd_file}, on traite toutes les frames.")
            max_frames = min_len
        else:
            max_frames = min(min_len, int(duration_sd * fps))

        print(f"Durée SD : {duration_sd:.2f}s, nombre frames max à traiter : {max_frames}")

        print("  Traitement frames...")
        for fname_hd, fname_sd in tqdm(zip(frames_hd[:max_frames], frames_sd[:max_frames]), total=max_frames):
            hd_img = cv2.imread(os.path.join(frames_hd_dir, fname_hd))
            sd_img = cv2.imread(os.path.join(frames_sd_dir, fname_sd))
            if hd_img is None or sd_img is None:
                print(f"  Impossible de lire {fname_hd} ou {fname_sd}, frame ignorée.")
                continue
            try:
                roi_sd = sd_img[y_sd:y_sd+h_sd_roi, x_sd:x_sd+w_sd_roi]
                roi_sd_resized = cv2.resize(roi_sd, (w_hd, h_hd), interpolation=cv2.INTER_LINEAR)
                hd_img[y_hd:y_hd+h_hd, x_hd:x_hd+w_hd] = roi_sd_resized
            except Exception as e:
                print(f"  Erreur frame {fname_hd}: {e}")
                continue
            cv2.imwrite(os.path.join(frames_out_dir, fname_hd), hd_img)

        output_path = os.path.join(output_folder, os.path.splitext(hd_file)[0] + "_no_watermark.mp4")
        rebuild_video_with_audio(frames_out_dir, audio_file, output_path, fps)

        print(f"Traitement terminé : {output_path}")

    print("\nToutes les vidéos traitées.")

if __name__ == "__main__":
    main()

# PatchToSD

PatchToSD is a Python tool that batch-processes HD videos to remove a watermark or overlay by replacing a defined region with the same area extracted from clean SD versions of the same videos.

---

## Features

- Replace a specific region in HD video frames with the matching region from the SD video
- Automatically matches HD/SD video pairs using a shared identifier in the filename
- Frame-accurate processing, synced to SD video duration
- Preserves HD audio from the original video
- Batch processing for multiple video files

---

## Use Case

You have HD videos with a watermark (like Center Parc's videos after you paid), and the same videos in lower-quality SD without the watermark.

PatchToSD allows you to:
- Select the watermark region once
- Automatically patch each frame in the HD video with clean data from the SD video
- Keep the original HD video quality and audio intact

### For Center Parc's videos, download each HD videos with the pink download button (official way) and right click on the video to download the SD version.

## Requirements

- Python 3.8+
- FFmpeg (installed and in PATH)
- Python libraries:
  pip install opencv-python tqdm

---

## How to Use

1. Place HD videos in videos_hd/ and SD videos in videos_sd/
2. Run the script:
   python PatchToSD.py
3. Select the watermark region using the graphical selector (mouse)
4. The tool will automatically patch all matching video pairs (by name)

---

## Technical Details

- Handles resolution differences by resizing SD patch to fit HD region
- Synchronizes to SD video duration to avoid outro/audio drift
- Uses HD audio for output
- Output format: .mp4 using H.264 (mp4v)

---

## Limitations

- Watermark must always be in the same screen position
- SD video must exactly match the HD one (same ID, same beginning)
- No motion watermark support

---

## License

This tool is provided for educational and personal use only.  
Do not use it to bypass copyright, licensing, or distribution rights.

---

## Author

GitHub: [https://github.com/xHookman](https://github.com/xHookman/)

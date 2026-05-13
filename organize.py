"""
City3D Data Organizer
=====================
Mengorganisir file input (point cloud + footprint) ke dalam
subfolder berdasarkan nama file (stem).

Contoh:
    Input folder berisi:
        bangunan_001.las
        bangunan_001.geojson
        bangunan_002.ply
        bangunan_002_footprint.obj
        bangunan_003.laz
        bangunan_003.obj

    Setelah dijalankan:
        output_folder/
            bangunan_001/
                bangunan_001.las
                bangunan_001.geojson
            bangunan_002/
                bangunan_002.ply
                bangunan_002_footprint.obj
            bangunan_003/
                bangunan_003.laz
                bangunan_003.obj

Supported formats:
    Point Cloud : .ply, .las, .laz
    Footprint   : .geojson, .obj

Usage:
    python organize.py                          ← pakai path di konfigurasi
    python organize.py <input_dir> <output_dir> ← override via command line
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

# ============================================================
# KONFIGURASI — sesuaikan path ini
# ============================================================

INPUT_DIR  = Path(r"C:\path\to\raw_input_folder")   # folder berisi semua file campur
OUTPUT_DIR = Path(r"C:\path\to\full_batch")          # folder output batch

# ============================================================

POINT_CLOUD_EXT = {".ply", ".las", ".laz"}
FOOTPRINT_EXT   = {".geojson", ".obj"}
ALL_EXT         = POINT_CLOUD_EXT | FOOTPRINT_EXT


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {
        "INFO":  "   ",
        "OK":    "[✓]",
        "ERROR": "[✗]",
        "SKIP":  "[~]",
        "WARN":  "[!]",
    }
    print(f"{ts} {icons.get(level, '   ')} {msg}")


def find_pc_stem(files):
    """
    Dari list file dalam satu grup, cari stem point cloud-nya.
    Point cloud stem = stem file .ply/.las/.laz
    """
    for f in files:
        if f.suffix.lower() in POINT_CLOUD_EXT:
            return f.stem
    return None


def group_files(input_dir):
    """
    Kelompokkan file berdasarkan stem point cloud-nya.

    Cara kerja:
    1. Scan semua file point cloud (.ply, .las, .laz) — ini jadi anchor/key
    2. Untuk tiap point cloud, cari file footprint yang namanya mengandung stem-nya
       - Exact match: bangunan_001.geojson
       - Flexible: bangunan_001_footprint.obj, bangunan_001_fp.obj, dst

    Return: dict { pc_stem: [list of Path files] }
    """
    all_files = [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in ALL_EXT]
    point_clouds = [f for f in all_files if f.suffix.lower() in POINT_CLOUD_EXT]
    others = [f for f in all_files if f.suffix.lower() in FOOTPRINT_EXT]

    groups = {}

    for pc in sorted(point_clouds):
        stem = pc.stem
        group = [pc]

        # Cari footprint yang namanya mengandung stem ini
        for fp in others:
            if stem.lower() in fp.stem.lower():
                group.append(fp)

        groups[stem] = group

    # Cek file footprint yang tidak ter-assign ke group manapun
    assigned = set()
    for files in groups.values():
        for f in files:
            assigned.add(f)

    unassigned = [f for f in others if f not in assigned]
    if unassigned:
        log(f"{len(unassigned)} file footprint tidak ter-assign:", "WARN")
        for f in unassigned:
            log(f"  {f.name}", "WARN")

    return groups


def organize(input_dir, output_dir):
    log(f"Input  : {input_dir}")
    log(f"Output : {output_dir}")
    print()

    if not input_dir.exists():
        log(f"Input folder tidak ditemukan: {input_dir}", "ERROR")
        return

    groups = group_files(input_dir)

    if not groups:
        log("Tidak ada file point cloud ditemukan.", "ERROR")
        return

    log(f"Ditemukan {len(groups)} bangunan untuk diorganisir")
    print()

    success = 0
    skipped = 0
    failed  = 0

    for stem, files in sorted(groups.items()):
        folder = output_dir / stem
        folder.mkdir(parents=True, exist_ok=True)

        pc_files = [f for f in files if f.suffix.lower() in POINT_CLOUD_EXT]
        fp_files = [f for f in files if f.suffix.lower() in FOOTPRINT_EXT]

        if not fp_files:
            log(f"'{stem}' — tidak ada footprint, diskip", "SKIP")
            skipped += 1
            continue

        try:
            for f in files:
                dest = folder / f.name
                if dest.exists():
                    log(f"  {f.name} sudah ada, diskip", "SKIP")
                    continue
                shutil.copy2(str(f), str(dest))

            log(f"'{stem}' → {folder.name}/ "
                f"({len(pc_files)} pc, {len(fp_files)} fp)", "OK")
            success += 1

        except Exception as e:
            log(f"'{stem}' GAGAL: {e}", "ERROR")
            failed += 1

    print()
    print("=" * 60)
    log(f"Selesai!")
    log(f"  Berhasil : {success}", "OK")
    if skipped:
        log(f"  Diskip   : {skipped} (tidak ada footprint)", "SKIP")
    if failed:
        log(f"  Gagal    : {failed}", "ERROR")
    print("=" * 60)
    print()
    log(f"Output siap di: {output_dir}")
    log(f"Sekarang bisa langsung dipakai sebagai BATCH_ROOT di city3d_batch.py")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        INPUT_DIR  = Path(sys.argv[1])
        OUTPUT_DIR = Path(sys.argv[2])
    elif len(sys.argv) != 1:
        print("Usage: python organize.py [input_dir] [output_dir]")
        sys.exit(1)

    organize(INPUT_DIR, OUTPUT_DIR)

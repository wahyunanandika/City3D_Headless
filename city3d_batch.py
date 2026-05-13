"""
City3D Batch Processor - Headless Mode
=======================================
Menjalankan City3D.exe dengan argumen command line langsung,
tanpa interaksi GUI sama sekali.

Requirements:
    Tidak perlu install library tambahan apapun.

Point Cloud : .ply, .las, .laz
Footprint   : .geojson (exact match), atau .obj (flexible — cari yang namanya mengandung stem pc)

Struktur folder INPUT:
    full_batch/
        B1/
            TIMUR1.las
            TIMUR1_footprint.obj
        B2/
            TIMUR2.ply
            TIMUR2.geojson
        ...

Struktur folder OUTPUT (otomatis dibuat, nama folder mirror input):
    full_batch/
        output/
            B1/
                TIMUR1_lod2.obj
            B2/
                TIMUR2_lod2.obj
            ...
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================================
# KONFIGURASI — sesuaikan path ini
# ============================================================

CITY3D_EXE = r"E:\04.Pak_ival\lib\build_city3d_shortcut\City3D\build\bin\City3D.exe"
BATCH_ROOT = Path(r"E:\04.Pak_ival\lib\build_city3d\T1")

# Polling interval (detik)
POLL_INTERVAL = 2
STARTUP_WAIT  = 2

# ============================================================


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {
        "INFO":    "   ",
        "OK":      "[✓]",
        "ERROR":   "[✗]",
        "SKIP":    "[~]",
        "SECTION": "===",
        "STEP":    " > ",
    }
    print(f"{ts} {icons.get(level, '   ')} {msg}")


# ============================================================
# JOB COLLECTION
# ============================================================

def find_footprint(batch_dir, pc_stem):
    """
    Cari file footprint untuk point cloud dengan nama pc_stem.

    Prioritas:
    1. Exact match .geojson
    2. Exact match .obj
    3. Flexible .geojson — nama mengandung pc_stem
    4. Flexible .obj     — nama mengandung pc_stem
    """
    fp = batch_dir / f"{pc_stem}.geojson"
    if fp.exists():
        return fp

    fp = batch_dir / f"{pc_stem}.obj"
    if fp.exists():
        return fp

    candidates = sorted([
        f for f in batch_dir.iterdir()
        if f.suffix.lower() == ".geojson" and pc_stem.lower() in f.stem.lower()
    ])
    if candidates:
        return candidates[0]

    candidates = sorted([
        f for f in batch_dir.iterdir()
        if f.suffix.lower() == ".obj" and pc_stem.lower() in f.stem.lower()
    ])
    if candidates:
        return candidates[0]

    return None


def collect_jobs(batch_dir, output_batch_dir):
    jobs = []

    point_clouds = sorted([
        f for f in batch_dir.iterdir()
        if f.suffix.lower() in (".ply", ".las", ".laz")
    ])

    for pc in point_clouds:
        name = pc.stem

        fp = find_footprint(batch_dir, name)
        if not fp:
            log(f"Tidak ada footprint untuk '{name}', diskip", "SKIP")
            continue

        out = output_batch_dir / f"{name}_lod2.obj"

        if out.exists():
            log(f"Output sudah ada untuk '{name}', diskip", "SKIP")
            continue

        log(f"  {pc.name} + {fp.name} → {out.name}", "INFO")
        jobs.append((pc, fp, out))

    return jobs


# ============================================================
# CORE: PROSES SATU BANGUNAN
# ============================================================

def process_one_building(pc_path, fp_path, out_path):
    """
    Jalankan City3D.exe headless untuk satu bangunan.
    Poll status file sampai selesai, lalu kill City3D.
    """
    status_file = Path(str(out_path) + ".status.txt")

    log(f"  Polling: {status_file}", "INFO")

    # Hapus status file lama kalau ada
    if status_file.exists():
        status_file.unlink()

    # Jalankan City3D headless
    proc = subprocess.Popen([
        str(CITY3D_EXE),
        str(pc_path),
        str(fp_path),
        str(out_path)
    ])

    time.sleep(STARTUP_WAIT)

    while True:
        # Cek status file
        if status_file.exists():
            try:
                status = status_file.read_text(encoding="utf-8").strip()
            except Exception:
                status = status_file.read_bytes().decode(errors="replace").strip()

            log(f"  Status: '{status}'", "INFO")

            if status == "done":
                # Kill City3D — tidak perlu tunggu user close manual
                proc.terminate()
                proc.wait()
                try:
                    status_file.unlink()
                except Exception:
                    pass
                return True

            elif status.startswith("error"):
                proc.terminate()
                proc.wait()
                try:
                    status_file.unlink()
                except Exception:
                    pass
                raise RuntimeError(status)

        # Cek apakah City3D sudah exit sendiri (crash)
        ret = proc.poll()
        if ret is not None and not status_file.exists():
            raise RuntimeError(f"City3D exit tanpa status file (return code: {ret})")

        time.sleep(POLL_INTERVAL)


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def run_batch():
    output_root = BATCH_ROOT / "output"

    batch_dirs = sorted([
        d for d in BATCH_ROOT.iterdir()
        if d.is_dir() and d.name != "output"
    ])

    if not batch_dirs:
        log(f"Tidak ada subfolder di: {BATCH_ROOT}", "ERROR")
        return

    all_batches = []
    for bd in batch_dirs:
        output_batch_dir = output_root / bd.name
        output_batch_dir.mkdir(parents=True, exist_ok=True)
        jobs = collect_jobs(bd, output_batch_dir)
        if jobs:
            all_batches.append((bd, output_batch_dir, jobs))
        else:
            log(f"Batch '{bd.name}': tidak ada job, diskip", "SKIP")

    if not all_batches:
        log("Tidak ada file untuk diproses.", "ERROR")
        return

    total_buildings = sum(len(j) for _, _, j in all_batches)

    print()
    print("=" * 60)
    log("CITY3D BATCH PROCESSOR — HEADLESS MODE", "SECTION")
    log(f"Input  : {BATCH_ROOT}")
    log(f"Output : {output_root}")
    log(f"Batch  : {len(all_batches)} folder")
    log(f"Total  : {total_buildings} bangunan")
    print("=" * 60)

    grand_success = 0
    grand_failed  = 0

    for batch_idx, (batch_dir, output_batch_dir, jobs) in enumerate(all_batches, 1):
        print()
        print("=" * 60)
        log(f"BATCH {batch_idx}/{len(all_batches)}: '{batch_dir.name}'  ({len(jobs)} bangunan)", "SECTION")
        log(f"Output → {output_batch_dir}")
        print("=" * 60)

        batch_success = 0
        batch_failed  = 0
        batch_start   = time.time()

        for building_idx, (pc, fp, out) in enumerate(jobs, 1):
            print()
            log(f"Bangunan {building_idx}/{len(jobs)}: '{pc.stem}' ({pc.suffix})")
            log(f"  PC       : {pc.name}")
            log(f"  Footprint: {fp.name}")
            log(f"  Output   : {out.name}")

            try:
                process_one_building(pc, fp, out)
                log(f"'{pc.stem}' selesai → {out.name}", "OK")
                batch_success += 1
                grand_success += 1
            except Exception as e:
                log(f"'{pc.stem}' GAGAL: {e}", "ERROR")
                batch_failed += 1
                grand_failed += 1

        elapsed = time.time() - batch_start
        mins, secs = divmod(int(elapsed), 60)
        print()
        print("-" * 60)
        log(f"Batch '{batch_dir.name}' selesai dalam {mins}m {secs}s", "OK")
        log(f"  Berhasil : {batch_success}/{len(jobs)}", "OK")
        if batch_failed:
            log(f"  Gagal    : {batch_failed}/{len(jobs)}", "ERROR")
        print("-" * 60)

    print()
    print("=" * 60)
    log("SEMUA BATCH SELESAI", "OK")
    log(f"  Total berhasil : {grand_success}/{total_buildings}", "OK")
    if grand_failed:
        log(f"  Total gagal    : {grand_failed}/{total_buildings}", "ERROR")
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) == 3:
        CITY3D_EXE = sys.argv[1]
        BATCH_ROOT = Path(sys.argv[2])
    elif len(sys.argv) != 1:
        print("Usage: python city3d_batch.py [City3D.exe] [full_batch_folder]")
        sys.exit(1)

    run_batch()

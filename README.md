# City3D Batch Processing

This repository extends [City3D](https://github.com/tudelft3d/City3D) with **headless batch processing** support — enabling automated reconstruction of multiple buildings without any GUI interaction.

> **Original project:** [City3D: Large-scale Building Reconstruction from Airborne LiDAR Point Clouds](https://github.com/tudelft3d/City3D)  
> All credits for the core reconstruction algorithm go to the original authors.

---

## What's Changed

Three source files were modified from the original City3D, and two Python scripts were added:

| File | Type | Description |
|------|------|-------------|
| `code/City3D/main.cpp` | Modified | Added headless mode — detects command line arguments |
| `code/City3D/main_window.h` | Modified | Added declarations for `runHeadless()` and `writeStatusFile()` |
| `code/City3D/main_window.cpp` | Modified | Added `runHeadless()`, `writeStatusFile()`, and keyboard shortcuts |
| `code/cmake/FindGUROBI.cmake` | Modified | Added support for Gurobi 1.3.0 and newer versions |
| `city3d_batch.py` | New | Python batch processor script |
| `organize.py` | New | Script to organize raw input files into batch folder structure |

### Headless Mode

City3D can now be run from the command line with three arguments:

```
City3D.exe <pointcloud> <footprint> <output>
```

When called this way, City3D will:
1. Load the point cloud
2. Load the footprint
3. Run segmentation
4. Extract roofs
5. Run reconstruction (using Gurobi if available)
6. Save the result directly to `<output>` without any dialog
7. Write a status file `<output>.status.txt` with `done` or `error: ...`
8. The Python script detects the status file and terminates City3D

When called without arguments, City3D runs normally as a GUI application — **fully backward compatible**.

### Keyboard Shortcuts Added

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open Point Cloud |
| `Ctrl+F` | Open Foot Print |
| `Ctrl+1` | Segmentation |
| `Ctrl+2` | Extract Roofs |
| `Ctrl+3` | Reconstruction |
| `Ctrl+S` | Save Reconstruction |

---

## Dependencies

> **Windows x64 only.** All dependencies must be for x64.

### 1. Visual Studio 2022 (or 2019)
Download: https://aka.ms/vs/17/release/vs_community.exe

### 2. CMake
Download: https://cmake.org/download/

### 3. CGAL (via vcpkg)

```bash
git clone https://github.com/microsoft/vcpkg
cd vcpkg
bootstrap-vcpkg.bat
vcpkg install cgal:x64-windows
```

### 4. OpenCV (via vcpkg)

```bash
vcpkg install opencv:x64-windows
```

### 5. Qt

Install Qt 5.15 or 6.x via Qt Online Installer. Select **MSVC 64-bit**.

### 6. Gurobi (recommended, faster than SCIP)

Download: https://www.gurobi.com/downloads/

> Requires academic license (free). Use your university email and university VPN.

Activate license:
```bash
grbgetkey <your-serial-number>
# Press Enter when asked for license location (auto-detected)
```

---

## Build Instructions

> Use **x64 Native Tools Command Prompt for VS** — not regular cmd.

### Step 1 — Set environment variables

```bash
set GUROBI_HOME=<path-to-gurobi>\win64
set PATH=%GUROBI_HOME%\bin;%PATH%
set Qt6_DIR=<path-to-qt6>\lib\cmake\Qt6
```

### Step 2 — Fix FindGUROBI.cmake

Edit `code/cmake/FindGUROBI.cmake`, change:

```cmake
find_library(GUROBI_C_LIBRARY
    NAMES gurobi120 gurobi100 libgurobi
    PATHS ${SEARCH_PATHS_FOR_LIBRARIES}
)
```

To:

```cmake
find_library(GUROBI_C_LIBRARY
    NAMES
        gurobi130
        gurobi120
        gurobi110
        gurobi100
        gurobi95
        libgurobi
    PATHS ${SEARCH_PATHS_FOR_LIBRARIES}
)
```

> This step is already applied in this repository's `FindGUROBI.cmake`.

### Step 3 — Build

```bash
cd <path-to-City3D>
mkdir build
cd build

cmake .. -G "NMake Makefiles" ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DCMAKE_TOOLCHAIN_FILE=<path-to-vcpkg>\scripts\buildsystems\vcpkg.cmake ^
  -DVCPKG_TARGET_TRIPLET=x64-windows ^
  -DQt6_DIR=%Qt6_DIR%

nmake
```

### Step 4 — Deploy Qt

Run `windeployqt` so City3D can find Qt DLLs:

```bash
cd <path-to-City3D>\build\bin
<path-to-qt6>\bin\windeployqt.exe City3D.exe
```

---

## Batch Processing

### Quick Start

If you just want to run the batch without building from source, download the prebuilt release from the [Releases](../../releases) page.

### Step 1 — Organize input files

If your input files are all in one folder (not yet sorted per building), use `organize.py`:

```bash
python organize.py <input_dir> <output_dir>
```

Example:
```
raw_input/
    bangunan_001.las
    bangunan_001.geojson
    bangunan_002.ply
    bangunan_002_footprint.obj
```

After running `organize.py`:
```
full_batch/
    bangunan_001/
        bangunan_001.las
        bangunan_001.geojson
    bangunan_002/
        bangunan_002.ply
        bangunan_002_footprint.obj
```

### Step 2 — Run batch

Edit the configuration at the top of `city3d_batch.py`:

```python
CITY3D_EXE = r"C:\path\to\City3D.exe"
BATCH_ROOT = Path(r"C:\path\to\full_batch")
```

Then run:

```bash
python city3d_batch.py

# Or override via command line
python city3d_batch.py "C:\path\City3D.exe" "C:\path\full_batch"
```

### Folder Structure

The batch script expects this structure:

```
full_batch/              ← BATCH_ROOT (folder name is flexible)
    batch_1/             ← subfolder name is flexible
        building_a.ply
        building_a.geojson
    batch_2/
        building_b.las
        building_b_footprint.obj
    ...
```

Output is automatically created:

```
full_batch/
    output/
        batch_1/
            building_a_lod2.obj
        batch_2/
            building_b_lod2.obj
```

### Supported Formats

| Type | Extensions |
|------|-----------|
| Point Cloud | `.ply`, `.las`, `.laz` |
| Footprint | `.geojson`, `.obj` |

Footprint matching is **flexible** — `building_a_footprint.obj` is automatically matched to `building_a.ply`.

### Features

- No GUI interaction — fully headless
- No extra Python dependencies required
- Resume support — skips buildings where output already exists
- Per-batch summary with elapsed time
- Crash detection

---

## Citation

If you use this work, please also cite the original City3D paper:

```bibtex
@Article{HuangCity3d_2022,
    AUTHOR = {Huang, Jin and Stoter, Jantien and Peters, Ravi and Nan, Liangliang},
    TITLE = {City3D: Large-Scale Building Reconstruction from Airborne LiDAR Point Clouds},
    JOURNAL = {Remote Sensing},
    VOLUME = {14},
    YEAR = {2022},
    NUMBER = {9},
    ARTICLE-NUMBER = {2254},
}
```

---

## License

This project follows the same license as the original City3D — GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

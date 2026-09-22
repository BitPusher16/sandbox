#!/usr/bin/env python3
"""
uv run python npy_to_mp4.py data/run_003.npy

Convert a fluid-sim .npy frame stack into a shareable H.264 MP4.

Frames are colorized and written to PNG in small batches (one batch in RAM
at a time). A second pass encodes the PNG sequence with ffmpeg, which also
does the nearest-neighbor upsample. Intermediate PNGs live next to the
output file and are removed after a successful encode.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

# =============================================================================
# Normalization.
#
# NORM_MODE:
#   "stdev"  — one global window from a first pass over fluid cells:
#                [mean - NORM_STDEV_LO * std,  mean + NORM_STDEV_HI * std]
#              Values outside clip. Lower the Nσ knobs to punch through a
#              quiet field; raise them to keep extrema on-scale.
#   "frame"  — each frame's own min/max, ignoring NORM_BORDER cells around
#              the outer edge (inlet / outlet / domain walls) and the solid.
# =============================================================================
NORM_MODE = "frame"
NORM_BORDER = 2
FPS = 60

#NORM_STDEV_LO = 2.0
#NORM_STDEV_HI = 2.0
NORM_STDEV_LO = 0.5
NORM_STDEV_HI = 0.5

# Sampled viridis stops (matplotlib), interpolated to 256 levels at runtime.
_VIRIDIS_STOPS = np.array(
    [
        [0.267004, 0.004874, 0.329415],
        [0.282327, 0.140938, 0.457517],
        [0.253935, 0.265254, 0.529983],
        [0.163625, 0.471133, 0.558148],
        [0.127568, 0.566949, 0.550556],
        [0.134692, 0.658636, 0.517649],
        [0.266941, 0.748751, 0.440573],
        [0.477504, 0.821444, 0.318195],
        [0.741388, 0.873449, 0.149561],
        [0.993248, 0.906157, 0.143936],
    ],
    dtype=np.float64,
)


def _viridis_lut() -> np.ndarray:
    n = 256
    x = np.linspace(0.0, 1.0, n)
    xp = np.linspace(0.0, 1.0, len(_VIRIDIS_STOPS))
    lut = np.column_stack([np.interp(x, xp, _VIRIDIS_STOPS[:, c]) for c in range(3)])
    return (lut * 255.0).round().astype(np.uint8)


def open_stack(path: Path) -> np.ndarray:
    data = np.load(path, mmap_mode="r", allow_pickle=True)
    if data.ndim not in (3, 4) and data.dtype != object:
        raise ValueError(
            f"{path} has shape {data.shape}; expected (T,H,W) or (T,H,W,C)"
        )
    return data


def n_frames_of(data: np.ndarray) -> int:
    return len(data) if data.dtype == object else int(data.shape[0])


def hw_of(data: np.ndarray) -> tuple[int, int]:
    frame0 = np.asarray(data[0])
    if frame0.ndim == 3:
        return int(frame0.shape[0]), int(frame0.shape[1])
    if frame0.ndim == 2:
        return int(frame0.shape[0]), int(frame0.shape[1])
    raise ValueError(f"frame 0 has shape {frame0.shape}; expected (H,W) or (H,W,C)")


def density_batch(data: np.ndarray, start: int, end: int) -> np.ndarray:
    """Load [start, end) frames and reduce D2Q9 populations to density."""
    if data.dtype == object:
        frames = np.stack([np.asarray(data[t], dtype=np.float64) for t in range(start, end)])
    else:
        frames = np.array(data[start:end], dtype=np.float64, copy=True)
    if frames.ndim == 4:
        return np.sum(frames, axis=-1)
    if frames.ndim == 3:
        return frames
    raise ValueError(f"batch has shape {frames.shape}; expected (T,H,W) or (T,H,W,C)")


def colorize_batch(
    fields: np.ndarray,
    vmin: float,
    vmax: float,
    wall: np.ndarray,
    lut: np.ndarray,
) -> np.ndarray:
    span = vmax - vmin
    t = np.clip((fields - vmin) / span, 0.0, 1.0)
    idx = (t * (len(lut) - 1)).astype(np.int64)
    rgb = lut[idx]
    rgb[:, wall] = 0
    return rgb


def interior_mask(height: int, width: int, border: int, wall: np.ndarray) -> np.ndarray:
    """True on fluid cells inside a NORM_BORDER margin on every side."""
    mask = np.ones((height, width), dtype=bool)
    b = max(int(border), 0)
    if b > 0:
        b_row = min(b, (height - 1) // 2)
        b_col = min(b, (width - 1) // 2)
        mask[:b_row, :] = False
        mask[-b_row:, :] = False
        mask[:, :b_col] = False
        mask[:, -b_col:] = False
    mask &= ~wall
    if not np.any(mask):
        mask = ~wall
        if not np.any(mask):
            mask = np.ones((height, width), dtype=bool)
    return mask


def colorize_batch_per_frame(
    fields: np.ndarray,
    wall: np.ndarray,
    lut: np.ndarray,
    border: int,
) -> np.ndarray:
    """Per-frame min/max over the interior; border and wall still get colored."""
    _, height, width = fields.shape
    interior = interior_mask(height, width, border, wall)
    masked = np.where(interior, fields, np.nan)
    vmin = np.nanmin(masked, axis=(1, 2), keepdims=True)
    vmax = np.nanmax(masked, axis=(1, 2), keepdims=True)
    span = vmax - vmin
    span = np.where(span > 0.0, span, 1.0)
    t = np.clip((fields - vmin) / span, 0.0, 1.0)
    idx = (t * (len(lut) - 1)).astype(np.int64)
    rgb = lut[idx]
    rgb[:, wall] = 0
    return rgb


def field_stats(
    data: np.ndarray,
    n_frames: int,
    batch_size: int,
    wall: np.ndarray,
) -> tuple[float, float, float, float]:
    """Global min, max, mean, std of fluid density (one batched pass)."""
    fluid = ~wall
    if not np.any(fluid):
        fluid = np.ones_like(wall, dtype=bool)
    count = 0
    total = 0.0
    total_sq = 0.0
    gmin = np.inf
    gmax = -np.inf
    for start in range(0, n_frames, batch_size):
        end = min(start + batch_size, n_frames)
        vals = density_batch(data, start, end)[:, fluid]
        count += int(vals.size)
        total += float(vals.sum())
        total_sq += float(np.square(vals).sum())
        gmin = min(gmin, float(vals.min()))
        gmax = max(gmax, float(vals.max()))
        print(f"stats {end}/{n_frames}", flush=True)
    mean = total / count
    var = max(total_sq / count - mean * mean, 0.0)
    std = float(np.sqrt(var))
    return float(gmin), float(gmax), float(mean), std


def colormap_limits(gmin: float, gmax: float, mean: float, std: float) -> tuple[float, float]:
    if std == 0.0:
        lo, hi = gmin, gmax
    else:
        lo = mean - NORM_STDEV_LO * std
        hi = mean + NORM_STDEV_HI * std
    vmin = max(lo, gmin)
    vmax = min(hi, gmax)
    if vmin >= vmax:
        vmin, vmax = gmin, gmax
        if vmin >= vmax:
            vmax = vmin + 1.0
    return vmin, vmax


def write_png_batches(
    data: np.ndarray,
    png_dir: Path,
    n_frames: int,
    batch_size: int,
    wall: np.ndarray,
    lut: np.ndarray,
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    import imageio.v2 as imageio

    png_dir.mkdir(parents=True, exist_ok=True)
    for start in range(0, n_frames, batch_size):
        end = min(start + batch_size, n_frames)
        fields = density_batch(data, start, end)
        if NORM_MODE == "frame":
            rgb = colorize_batch_per_frame(fields, wall, lut, NORM_BORDER)
        else:
            assert vmin is not None and vmax is not None
            rgb = colorize_batch(fields, vmin, vmax, wall, lut)
        for i, frame in enumerate(rgb):
            t = start + i
            imageio.imwrite(png_dir / f"frame_{t:06d}.png", frame)
        print(f"png {end}/{n_frames}", flush=True)
        del fields, rgb


def encode_png_sequence(png_dir: Path, out: Path, fps: int, out_h: int, out_w: int) -> None:
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pattern = png_dir / "frame_%06d.png"
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-stats",
        "-framerate",
        str(fps),
        "-i",
        str(pattern),
        "-vf",
        f"scale={out_w}:{out_h}:flags=neighbor",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-movflags",
        "+faststart",
        str(out),
    ]
    print(f"encoding {out} ...", flush=True)
    subprocess.run(cmd, check=True)


def auto_scale(height: int, width: int, target_long: int = 1024) -> int:
    return max(1, target_long // max(height, width))


def even(n: int) -> int:
    return n if n % 2 == 0 else n + 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "npy",
        nargs="?",
        default="data/run_002.npy",
        type=Path,
        help="input .npy frame stack (default: data/run_002.npy)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output .mp4 path (default: alongside the .npy)",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=None,
        help="nearest-neighbor upsample factor (default: longest side ~1024)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="frames to colorize and write per batch",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="leave the intermediate PNG directory in place after encoding",
    )
    args = parser.parse_args()

    src = args.npy
    out = args.output if args.output is not None else src.with_suffix(".mp4")
    png_dir = out.parent / f".{out.stem}_frames"
    out.parent.mkdir(parents=True, exist_ok=True)

    data = open_stack(src)
    n_frames = n_frames_of(data)
    height, width = hw_of(data)
    scale = args.scale if args.scale is not None else auto_scale(height, width)
    out_h = even(height * scale)
    out_w = even(width * scale)

    wall = density_batch(data, 0, 1)[0] == 0
    if not np.any(~wall):
        wall = np.zeros((height, width), dtype=bool)

    vmin: float | None = None
    vmax: float | None = None
    if NORM_MODE == "stdev":
        gmin, gmax, mean, std = field_stats(data, n_frames, args.batch_size, wall)
        vmin, vmax = colormap_limits(gmin, gmax, mean, std)
        print(
            f"density min={gmin:.6g} max={gmax:.6g} mean={mean:.6g} std={std:.6g}",
            flush=True,
        )
        print(
            f"colormap [{mean:.6g} - {NORM_STDEV_LO}*std, "
            f"{mean:.6g} + {NORM_STDEV_HI}*std] -> [{vmin:.6g}, {vmax:.6g}]",
            flush=True,
        )
    elif NORM_MODE == "frame":
        print(
            f"colormap per-frame min/max, border={NORM_BORDER} cells",
            flush=True,
        )
    else:
        raise ValueError(f"NORM_MODE={NORM_MODE!r}; expected 'stdev' or 'frame'")

    lut = _viridis_lut()

    try:
        write_png_batches(
            data,
            png_dir,
            n_frames,
            args.batch_size,
            wall,
            lut,
            vmin=vmin,
            vmax=vmax,
        )
        encode_png_sequence(png_dir, out, FPS, out_h, out_w)
    except subprocess.CalledProcessError as exc:
        print(
            f"ffmpeg failed (exit {exc.returncode}); PNGs kept in {png_dir}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    else:
        if not args.keep_frames:
            shutil.rmtree(png_dir, ignore_errors=True)

    duration = n_frames / FPS
    print(
        f"wrote {out}  ({n_frames} frames, {height}x{width} lattice "
        f"upscaled {scale}x to {out_h}x{out_w}, "
        f"{FPS} fps, {duration:.1f}s)"
    )


if __name__ == "__main__":
    main()

from typing import Any, Callable, Dict, List, Optional

try:
    import rustism

    HAS_RUSTISM = True
except ImportError as e:
    print(f"Warning: rustism module not available: {e}")
    HAS_RUSTISM = False
    rustism = None


def get_sequential(
    width: int = 800,
    height: int = 600,
    tile_w: int = 64,
    tile_h: int = 64,
    max_iter: int = 256,
    emit_callback: Optional[Callable] = None,
    time_limit_ms: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Execute sequential Mandelbrot tile rendering using Rust backend.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        tile_w: Tile width for processing
        tile_h: Tile height for processing
        max_iter: Maximum iterations for Mandelbrot calculation
        emit_callback: Optional callback function for tile updates
        time_limit_ms: Time limit in milliseconds

    Returns:
        List of task records with performance metrics
    """
    if not HAS_RUSTISM:
        raise RuntimeError("Rustism module is not available")

    # use a no-op callback if none provided
    if emit_callback is None:
        emit_callback = lambda tile: None

    # Call the Rust function with all params
    task_records = rustism.sequential(
        width=width,
        height=height,
        tile_w=tile_w,
        tile_h=tile_h,
        max_iter=max_iter,
        emit_tile=emit_callback,
        time_limit_ms=time_limit_ms,
    )

    return task_records


def get_concurrent(
    width: int = 800,
    height: int = 600,
    tile_w: int = 64,
    tile_h: int = 64,
    max_iter: int = 256,
    emit_callback: Optional[Callable] = None,
    time_limit_ms: int = 2000,
    num_threads: int = 4,
) -> List[Dict[str, Any]]:
    """
    Execute concurrent Mandelbrot tile rendering using Rust backend with multiple threads.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        tile_w: Tile width for processing
        tile_h: Tile height for processing
        max_iter: Maximum iterations for Mandelbrot calculation
        emit_callback: Optional callback function for tile updates
        time_limit_ms: Time limit in milliseconds
        num_threads: Number of threads to use for parallel processing

    Returns:
        List of task records with performance metrics
    """
    if not HAS_RUSTISM:
        raise RuntimeError("Rustism module is not available")

    # use a no-op callback if none provided
    if emit_callback is None:
        emit_callback = lambda tile: None

    # Call the Rust function with all params
    task_records = rustism.concurrent(
        width=width,
        height=height,
        tile_w=tile_w,
        tile_h=tile_h,
        max_iter=max_iter,
        emit_tile=emit_callback,
        time_limit_ms=time_limit_ms,
        num_threads=num_threads,
    )

    return task_records


def is_rustism_available() -> bool:
    """
    Check if the Rustism module is available and loaded.

    Returns:
        True if rustism is available, False otherwise
    """
    return HAS_RUSTISM

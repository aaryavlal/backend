from typing import Any, Callable, Dict, List, Optional

import rustism


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
    TODO: docs
    """

    # use a no op callback if none provided
    if emit_callback is None:
        emit_callback = lambda title: None

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
    num_threads: int = 4,  # should change later depending on system we are deploying to
) -> List[Dict[str, Any]]:
    """
    TODO: docs
    """

    # use a no op callback if none provided
    if emit_callback is None:
        emit_callback = lambda title: None

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

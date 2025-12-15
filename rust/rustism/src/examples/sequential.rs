use crate::model::{TaskRecord, TileUpdate, render_tile};
use pyo3::prelude::*;
use std::time::{Duration, Instant};

#[pyfunction]
pub fn sequential(
    py: Python<'_>,
    width: usize,
    height: usize,
    tile_w: usize,
    tile_h: usize,
    max_iter: u16,
    emit_tile: PyObject,
    time_limit_ms: u64,
) -> PyResult<Vec<TaskRecord>> {
    let mut records = Vec::new();
    let mut task_id = 0;

    let overall_start = Instant::now();
    let time_limit = Duration::from_millis(time_limit_ms);

    for ty in (0..height).step_by(tile_h) {
        for tx in (0..width).step_by(tile_w) {
            // Check if we've exceeded the time limit
            if overall_start.elapsed() >= time_limit {
                break;
            }

            let start = Instant::now();

            let data = render_tile(width, height, tx, ty, tile_w, tile_h, max_iter);

            let duration_ms = start.elapsed().as_millis();

            emit_tile.call1(
                py,
                (TileUpdate {
                    task_id,
                    tile_x: tx as u32,
                    tile_y: ty as u32,
                    tile_w: tile_w as u32,
                    tile_h: tile_h as u32,
                    data,
                    duration_ms,
                },),
            )?;

            records.push(TaskRecord {
                task_id,
                tile_x: tx as u32,
                tile_y: ty as u32,
                tile_w: tile_w as u32,
                tile_h: tile_h as u32,
                duration_ms,
                pixels_computed: (tile_w * tile_h) as u32,
            });

            task_id += 1;

            // Also check at the end of each row
            if overall_start.elapsed() >= time_limit {
                break;
            }
        }
    }

    Ok(records)
}

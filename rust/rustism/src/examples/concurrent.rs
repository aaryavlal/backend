use crate::model::{TaskRecord, TileUpdate, render_tile};
use pyo3::prelude::*;
use std::{
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    time::{Duration, Instant},
};

#[pyfunction]
pub fn concurrent(
    py: Python<'_>,
    width: usize,
    height: usize,
    tile_w: usize,
    tile_h: usize,
    max_iter: u16,
    emit_tile: PyObject,
    time_limit_ms: u64,
    num_threads: usize,
) -> PyResult<Vec<TaskRecord>> {
    // Collect all tile coordinates first
    let mut tiles = Vec::new();
    for ty in (0..height).step_by(tile_h) {
        for tx in (0..width).step_by(tile_w) {
            tiles.push((tx, ty));
        }
    }

    let overall_start = Instant::now();
    let time_limit = Duration::from_millis(time_limit_ms);

    // Shared state for time limit checking
    let time_exceeded = Arc::new(AtomicBool::new(false));
    // Shared state for collecting results
    let records = Arc::new(Mutex::new(Vec::new()));

    // Scoped threads to share references during computations
    std::thread::scope(|s| {
        // Divide work among threads
        let chunk_size = (tiles.len() + num_threads - 1) / num_threads;

        for (worked_id, tile_chunk) in tiles.chunks(chunk_size).enumerate() {
            let time_exceeded = Arc::clone(&time_exceeded);
            let records = Arc::clone(&records);

            // Spawn a shared thread for this chunk of tiles
            s.spawn(move || {
                for &(tx, ty) in tile_chunk {
                    // Check if TLE
                    if time_exceeded.load(Ordering::Relaxed) {
                        break;
                    }

                    // Check TL
                    if overall_start.elapsed() > time_limit {
                        time_exceeded.store(true, Ordering::Relaxed);
                        break;
                    }

                    let start = Instant::now();
                    let task_id = worked_id
                        + chunk_size
                        + tile_chunk.iter().position(|&pos| pos == (tx, ty)).unwrap();

                    let data = render_tile(width, height, tx, ty, tile_w, tile_h, max_iter);
                    let duration_ms = start.elapsed().as_millis();

                    // Store the result
                    let record = TaskRecord {
                        task_id: task_id as u32,
                        tile_x: tx as u32,
                        tile_y: ty as u32,
                        tile_w: tile_w as u32,
                        tile_h: tile_h as u32,
                        duration_ms,
                        pixels_computed: (tile_w * tile_h) as u32,
                    };

                    // Lock and push to shared records
                    records
                        .lock()
                        .unwrap()
                        .push((record, data, duration_ms, tx, ty));
                }
            });
        }
    });

    // Now emit all tiles to Python (via main thread)
    let mut results = Arc::try_unwrap(records)
        .expect("Failed to unwrap Arc")
        .into_inner()
        .unwrap();

    // Sort by task_id to maintain order
    results.sort_by_key(|(record, _, _, _, _)| record.task_id);

    let mut final_records = Vec::new();
    for (record, data, duration_ms, tx, ty) in results {
        emit_tile.call1(
            py,
            (TileUpdate {
                task_id: record.task_id,
                tile_x: tx as u32,
                tile_y: ty as u32,
                tile_w: tile_w as u32,
                tile_h: tile_h as u32,
                data,
                duration_ms,
            },),
        )?;
        final_records.push(record);
    }

    Ok(final_records)
}

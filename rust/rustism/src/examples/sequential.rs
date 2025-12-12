use crate::{TIME_MULTIPLIER, model::TaskRecord};
use pyo3::prelude::*;
use std::time::{Duration, Instant};

fn task() {
    std::thread::sleep(Duration::from_millis(100));
}

#[pyfunction]
pub fn sequential() -> Vec<TaskRecord> {
    let start = Instant::now();
    let mut tasks = Vec::new();
    for task_id in 1..=3 {
        let start_ms = start.elapsed().as_millis() * TIME_MULTIPLIER;
        task();
        let end_ms = start.elapsed().as_millis() * TIME_MULTIPLIER;
        let duration_ms = end_ms - start_ms;
        tasks.push(TaskRecord::new(task_id, start_ms, end_ms, duration_ms))
    }
    tasks
}

use pyo3::IntoPyObject;
use pyo3::prelude::*;

#[derive(Debug, IntoPyObject)]
pub struct TaskRecord {
    pub task_id: u32,
    pub start_ms: u128,
    pub end_ms: u128,
    pub duration_ms: u128,
}

impl TaskRecord {
    pub fn new(task_id: u32, start_ms: u128, end_ms: u128, duration_ms: u128) -> Self {
        TaskRecord {
            task_id,
            start_ms,
            end_ms,
            duration_ms,
        }
    }
}

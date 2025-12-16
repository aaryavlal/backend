pub mod examples;
pub mod model;

use pyo3::prelude::*;

pub const TIME_MULTIPLIER: u128 = 5;

#[pymodule]
fn rustism(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(examples::sequential::sequential, m)?)?;
    m.add_function(wrap_pyfunction!(examples::concurrent::concurrent, m)?)?;
    Ok(())
}

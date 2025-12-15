use pyo3::IntoPyObject;
use pyo3::prelude::*;

#[derive(Debug, IntoPyObject)]
pub struct TaskRecord {
    pub task_id: u32,
    pub tile_x: u32,
    pub tile_y: u32,
    pub tile_w: u32,
    pub tile_h: u32,
    pub duration_ms: u128,
    pub pixels_computed: u32,
}

#[derive(IntoPyObject)]
pub struct TileUpdate {
    pub task_id: u32,
    pub tile_x: u32,
    pub tile_y: u32,
    pub tile_w: u32,
    pub tile_h: u32,
    pub data: Vec<u16>, // iteration counts
    pub duration_ms: u128,
}

pub fn render_tile(
    width: usize,
    height: usize,
    tile_x: usize,
    tile_y: usize,
    tile_w: usize,
    tile_h: usize,
    max_iter: u16,
) -> Vec<u16> {
    let mut out = Vec::with_capacity(tile_w * tile_h);

    for dy in 0..tile_h {
        let y = tile_y + dy;
        if y >= height {
            break;
        }

        for dx in 0..tile_w {
            let x = tile_x + dx;
            if x >= width {
                break;
            }

            let c_re = (x as f64 / width as f64) * 3.5 - 2.5;
            let c_im = (y as f64 / height as f64) * 2.0 - 1.0;

            out.push(mandelbrot(c_re, c_im, max_iter));
        }
    }

    out
}

#[inline(always)]
pub fn mandelbrot(c_re: f64, c_im: f64, max_iter: u16) -> u16 {
    let mut z_re = 0.0;
    let mut z_im = 0.0;

    for i in 0..max_iter {
        let re2 = z_re * z_re;
        let im2 = z_im * z_im;

        if re2 + im2 > 4.0 {
            return i;
        }

        z_im = 2.0 * z_re * z_im + c_im;
        z_re = re2 - im2 + c_re;
    }

    max_iter
}

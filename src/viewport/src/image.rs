use eframe::egui::Vec2;

pub(crate) const RENDER_PIXELS_MAX: u64 = 64_000_000;

const PNG_SIGNATURE: &[u8; 8] = b"\x89PNG\r\n\x1a\n";
const PNG_COLOR_TYPE_RGBA: u8 = 6;
const PNG_BIT_DEPTH_8: u8 = 8;
const PNG_COMPRESSION_DEFLATE: u8 = 0;
const PNG_FILTER_NONE: u8 = 0;
const PNG_INTERLACE_NONE: u8 = 0;

/// Encode RGBA8 pixels as PNG bytes.
pub fn encode_rgba_png(width: u32, height: u32, rgba: &[u8]) -> Result<Vec<u8>, String> {
    encode_png(width, height, rgba)
}

/// Wrap PNG bytes in an SVG image element.
pub fn embedded_png_svg(
    width: u32,
    height: u32,
    title: &str,
    png: &[u8],
) -> Result<String, String> {
    if width == 0 || height == 0 {
        return Err("svg size must be non-zero".to_owned());
    }
    if u64::from(width) * u64::from(height) > RENDER_PIXELS_MAX {
        return Err(format!("svg image is too large: {width} x {height}"));
    }
    if !png.starts_with(PNG_SIGNATURE) {
        return Err("embedded svg image must be png data".to_owned());
    }

    let encoded = base64_encode(png);
    let mut svg = String::new();
    svg.push_str(r#"<?xml version="1.0" encoding="UTF-8"?>"#);
    svg.push('\n');
    svg.push_str(&format!(
        r#"<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">"#
    ));
    svg.push('\n');
    svg.push_str("  <title>");
    push_xml_escaped(&mut svg, title);
    svg.push_str("</title>\n");
    svg.push_str(r##"  <rect width="100%" height="100%" fill="#FFFFFF"/>"##);
    svg.push('\n');
    svg.push_str(&format!(
        r#"  <image x="0" y="0" width="{width}" height="{height}" href="data:image/png;base64,{encoded}" preserveAspectRatio="none"/>"#
    ));
    svg.push_str("\n</svg>\n");
    Ok(svg)
}

pub(crate) fn capture_size_for_canvas(
    canvas_width: u32,
    canvas_height: u32,
    view_size: Vec2,
) -> (u32, u32) {
    let viewport_width = view_size.x.max(1.0);
    let viewport_height = view_size.y.max(1.0);
    let viewport_ratio = viewport_width / viewport_height;
    let canvas_ratio = canvas_width as f32 / canvas_height as f32;

    if viewport_ratio >= canvas_ratio {
        let capture_width = canvas_width;
        let capture_height = ((capture_width as f32 / viewport_ratio).round() as u32).max(1);
        (capture_width, capture_height)
    } else {
        let capture_height = canvas_height;
        let capture_width = ((capture_height as f32 * viewport_ratio).round() as u32).max(1);
        (capture_width, capture_height)
    }
}

pub(crate) fn center_on_canvas(
    canvas_width: u32,
    canvas_height: u32,
    image_width: u32,
    image_height: u32,
    image_rgba: &[u8],
) -> Result<Vec<u8>, String> {
    let canvas_width_usize =
        usize::try_from(canvas_width).map_err(|_| "invalid canvas width".to_owned())?;
    let canvas_height_usize =
        usize::try_from(canvas_height).map_err(|_| "invalid canvas height".to_owned())?;
    let image_width_usize =
        usize::try_from(image_width).map_err(|_| "invalid image width".to_owned())?;
    let image_height_usize =
        usize::try_from(image_height).map_err(|_| "invalid image height".to_owned())?;
    let image_stride = image_width_usize
        .checked_mul(4)
        .ok_or_else(|| "image row is too large".to_owned())?;
    let image_size = image_stride
        .checked_mul(image_height_usize)
        .ok_or_else(|| "image is too large".to_owned())?;
    if image_rgba.len() != image_size {
        return Err("image buffer has invalid length".to_owned());
    }

    let canvas_stride = canvas_width_usize
        .checked_mul(4)
        .ok_or_else(|| "canvas row is too large".to_owned())?;
    let canvas_size = canvas_stride
        .checked_mul(canvas_height_usize)
        .ok_or_else(|| "canvas is too large".to_owned())?;
    let mut canvas = vec![255_u8; canvas_size];
    let x_offset = (canvas_width_usize.saturating_sub(image_width_usize)) / 2;
    let y_offset = (canvas_height_usize.saturating_sub(image_height_usize)) / 2;

    for row in 0..image_height_usize {
        let src_start = row * image_stride;
        let src_end = src_start + image_stride;
        let dst_start = (row + y_offset) * canvas_stride + x_offset * 4;
        let dst_end = dst_start + image_stride;
        if dst_end > canvas.len() {
            return Err("image does not fit on export canvas".to_owned());
        }
        canvas[dst_start..dst_end].copy_from_slice(&image_rgba[src_start..src_end]);
    }
    Ok(canvas)
}

pub(crate) fn encode_png(width: u32, height: u32, rgba: &[u8]) -> Result<Vec<u8>, String> {
    let row_bytes = usize::try_from(width)
        .map_err(|_| "invalid png width".to_owned())?
        .checked_mul(4)
        .ok_or_else(|| "png row is too large".to_owned())?;
    let expected_len = row_bytes
        .checked_mul(usize::try_from(height).map_err(|_| "invalid png height".to_owned())?)
        .ok_or_else(|| "png image is too large".to_owned())?;
    if rgba.len() != expected_len {
        return Err("png pixel buffer has invalid length".to_owned());
    }

    let height_usize = usize::try_from(height).map_err(|_| "invalid png height".to_owned())?;
    let mut raw = Vec::with_capacity(expected_len + height_usize);
    for row in rgba.chunks_exact(row_bytes) {
        raw.push(PNG_FILTER_NONE);
        raw.extend_from_slice(row);
    }

    let mut encoder = flate2::write::ZlibEncoder::new(Vec::new(), flate2::Compression::fast());
    std::io::Write::write_all(&mut encoder, &raw).map_err(|err| err.to_string())?;
    let compressed = encoder.finish().map_err(|err| err.to_string())?;

    let mut png = Vec::new();
    png.extend_from_slice(PNG_SIGNATURE);
    let mut ihdr = Vec::with_capacity(13);
    ihdr.extend_from_slice(&width.to_be_bytes());
    ihdr.extend_from_slice(&height.to_be_bytes());
    ihdr.push(PNG_BIT_DEPTH_8);
    ihdr.push(PNG_COLOR_TYPE_RGBA);
    ihdr.push(PNG_COMPRESSION_DEFLATE);
    ihdr.push(PNG_FILTER_NONE);
    ihdr.push(PNG_INTERLACE_NONE);
    write_png_chunk(&mut png, b"IHDR", &ihdr)?;
    write_png_chunk(&mut png, b"IDAT", &compressed)?;
    write_png_chunk(&mut png, b"IEND", &[])?;
    Ok(png)
}

fn push_xml_escaped(out: &mut String, value: &str) {
    for ch in value.chars() {
        match ch {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            '"' => out.push_str("&quot;"),
            '\'' => out.push_str("&apos;"),
            _ => out.push(ch),
        }
    }
}

fn base64_encode(bytes: &[u8]) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let b0 = chunk[0];
        let b1 = chunk.get(1).copied().unwrap_or(0);
        let b2 = chunk.get(2).copied().unwrap_or(0);

        out.push(TABLE[(b0 >> 2) as usize] as char);
        out.push(TABLE[(((b0 & 0x03) << 4) | (b1 >> 4)) as usize] as char);
        if chunk.len() > 1 {
            out.push(TABLE[(((b1 & 0x0f) << 2) | (b2 >> 6)) as usize] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(TABLE[(b2 & 0x3f) as usize] as char);
        } else {
            out.push('=');
        }
    }
    out
}

fn write_png_chunk(out: &mut Vec<u8>, kind: &[u8; 4], data: &[u8]) -> Result<(), String> {
    out.extend_from_slice(
        &u32::try_from(data.len())
            .map_err(|_| "png chunk is too large".to_owned())?
            .to_be_bytes(),
    );
    out.extend_from_slice(kind);
    out.extend_from_slice(data);
    let mut hasher = crc32fast::Hasher::new();
    hasher.update(kind);
    hasher.update(data);
    out.extend_from_slice(&hasher.finalize().to_be_bytes());
    Ok(())
}

mod app;
mod export;
mod model;
mod viewport;

use eframe::egui;

rust_i18n::i18n!("locales", fallback = "en");

fn main() -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("GDS3D")
            .with_inner_size([1280.0, 820.0]),
        ..Default::default()
    };

    eframe::run_native(
        "GDS3D",
        options,
        Box::new(|cc| Ok(Box::new(app::Gds3dApp::new(cc)))),
    )
}

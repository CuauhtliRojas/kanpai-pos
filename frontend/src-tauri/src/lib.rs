use std::{
    net::TcpListener,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
};

use tauri::{path::BaseDirectory, Manager};

const SIDECAR_BINARY_NAME: &str = "kanpai-api.exe";

#[derive(Clone)]
struct ApiRuntimeState {
    base_url: String,
}

#[tauri::command]
fn get_api_base_url(state: tauri::State<'_, ApiRuntimeState>) -> String {
    state.base_url.clone()
}

fn pick_available_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0")
        .expect("no se pudo reservar un puerto local para Kanpai API");
    listener
        .local_addr()
        .expect("no se pudo leer el puerto local reservado")
        .port()
}

fn resolve_sidecar_path(app: &tauri::AppHandle) -> Result<PathBuf, Box<dyn std::error::Error>> {
    if let Ok(resource_path) = app.path().resolve(
        format!("binaries/{SIDECAR_BINARY_NAME}"),
        BaseDirectory::Resource,
    ) {
        if resource_path.exists() {
            return Ok(resource_path);
        }
    }

    let current_dir = std::env::current_dir()?;
    let candidates = [
        current_dir.join("binaries").join(SIDECAR_BINARY_NAME),
        current_dir
            .join("frontend")
            .join("src-tauri")
            .join("binaries")
            .join(SIDECAR_BINARY_NAME),
        current_dir
            .parent()
            .unwrap_or(&current_dir)
            .join("src-tauri")
            .join("binaries")
            .join(SIDECAR_BINARY_NAME),
    ];

    for candidate in candidates {
        if candidate.exists() {
            return Ok(candidate);
        }
    }

    Err(std::io::Error::new(
        std::io::ErrorKind::NotFound,
        format!("no se encontro el sidecar {SIDECAR_BINARY_NAME}"),
    )
    .into())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let api_port = pick_available_port();
    let api_base_url = format!("http://127.0.0.1:{api_port}");
    let api_process: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));

    let runtime_state = ApiRuntimeState {
        base_url: api_base_url,
    };

    let setup_process = api_process.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(runtime_state)
        .setup(move |app| {
            let sidecar_path = resolve_sidecar_path(app.handle())?;

            let child = Command::new(&sidecar_path)
                .env("KANPAI_API_PORT", api_port.to_string())
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|error| {
                    std::io::Error::new(
                        std::io::ErrorKind::Other,
                        format!(
                            "no se pudo iniciar el backend Kanpai API en {}: {error}",
                            sidecar_path.display()
                        ),
                    )
                })?;

            if let Ok(mut guard) = setup_process.lock() {
                *guard = Some(child);
            }

            Ok(())
        })
        .on_window_event(move |_window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Ok(mut guard) = api_process.lock() {
                    if let Some(mut child) = guard.take() {
                        let _ = child.kill();
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![get_api_base_url])
        .run(tauri::generate_context!())
        .expect("error while running Kanpai POS");
}


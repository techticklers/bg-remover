import io
import time
import zipfile
from pathlib import Path
from PIL import Image
import streamlit as st

from processor import process_image
from batch_manager import (
    SUPPORTED_EXTENSIONS,
    scan_images,
    check_path_overlap,
    open_folder_in_os,
    DirectoryLock,
    BatchProgressTracker,
    setup_logger,
    format_duration
)
from hardware import (
    detect_hardware,
    resolve_execution_provider,
    create_rembg_session
)

# Page configuration
st.set_page_config(
    page_title="Bulk Background Remover Studio",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Modern Dark Theme styling with high contrast readability
st.markdown("""
<style>
    /* Global Typography & Background adjustments */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    /* Clean Header */
    .header-container {
        padding: 1.2rem 1.5rem;
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .header-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .header-tagline {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-top: 0.25rem;
    }
    
    /* Stats Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 0.8rem;
        margin-bottom: 1.2rem;
    }
    .stat-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 0.9rem;
        text-align: center;
    }
    .stat-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #38BDF8;
    }
    .stat-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-top: 0.2rem;
    }
    
    /* Device Pill */
    .device-badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        background-color: #0369A1;
        color: #E0F2FE;
        border: 1px solid #38BDF8;
    }

    /* Preview Frame */
    .preview-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Hardware Detection
hw_info = detect_hardware()

# Initialize Session State
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "cancel_requested" not in st.session_state:
    st.session_state.cancel_requested = False
if "batch_summary" not in st.session_state:
    st.session_state.batch_summary = None
if "recent_errors" not in st.session_state:
    st.session_state.recent_errors = []

# Cached AI Model Loader
@st.cache_resource(show_spinner="Initializing AI Model (Local ONNX Session)...")
def get_cached_session(provider_key: str):
    dev_name, providers, _ = resolve_execution_provider(provider_key)
    return create_rembg_session(model_name="u2net", providers=providers)


def main():
    # Top Professional Header
    st.markdown(f"""
    <div class="header-container">
        <div>
            <div class="header-title">✂️ Bulk Background Remover Studio</div>
            <div class="header-tagline">High-volume product photo background removal, auto-centering, and format export.</div>
        </div>
        <div>
            <span class="device-badge">OS: {hw_info['os']} ({hw_info['arch']})</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # SIDEBAR: Engine Hardware & Processing Configuration
    # -------------------------------------------------------------
    st.sidebar.header("⚡ Hardware & Acceleration")
    
    device_choice = st.sidebar.selectbox(
        "Processing Device",
        options=["Auto", "CPU", "GPU (CUDA)"],
        index=0,
        help="Select processing provider. 'Auto' will detect NVIDIA CUDA if onnxruntime-gpu and CUDA are configured; otherwise defaults to CPU."
    )

    active_device_label, active_providers, dev_msg = resolve_execution_provider(device_choice)
    st.sidebar.caption(f"**Active Engine**: `{active_device_label}`")
    if "⚠️" in dev_msg:
        st.sidebar.warning(dev_msg)
    else:
        st.sidebar.success(dev_msg)

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Canvas & Output Settings")

    canvas_dim = st.sidebar.number_input(
        "Canvas Dimensions (px)",
        min_value=500,
        max_value=5000,
        value=2000,
        step=100,
        help="Target square canvas size (default: 2000 for 2000x2000)"
    )
    
    padding_pct = st.sidebar.slider(
        "Product Padding (%)",
        min_value=0,
        max_value=40,
        value=10,
        step=1,
        help="Margin around product inside the canvas (10% leaves 80% product footprint)"
    ) / 100.0

    export_format = st.sidebar.selectbox(
        "Export Format",
        options=["both", "transparent", "white"],
        format_func=lambda x: {
            "both": "Both (Transparent PNG + White JPG)",
            "transparent": "Transparent PNG Only",
            "white": "White Background JPG Only"
        }[x]
    )

    jpg_quality = st.sidebar.slider(
        "JPG Quality",
        min_value=50,
        max_value=100,
        value=95,
        step=1,
        help="Compression quality for white-background JPG images"
    )

    skip_completed = st.sidebar.checkbox(
        "Skip previously processed images",
        value=True,
        help="Resumes interrupted batches without re-processing completed images (validates matching settings)"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("🔒 **Security & Commercial License**:\n- 100% Localhost offline execution\n- Zero cloud telemetry or external uploads\n- Permissive commercial license (Apache 2.0 / MIT)")

    # -------------------------------------------------------------
    # MAIN WORKSPACE TABS
    # -------------------------------------------------------------
    tab_folder, tab_upload = st.tabs(["📁 Local Folder Mode (500 - 5,000+ images)", "📤 File Upload Mode (Interactive Upload)"])

    # -------------------------------------------------------------
    # TAB 1: Local Folder Processing
    # -------------------------------------------------------------
    with tab_folder:
        col_inp, col_out = st.columns(2)
        with col_inp:
            input_dir_str = st.text_input(
                "Input Folder Path",
                placeholder="Windows: C:\\Photos\\Raw  |  Mac: /Users/name/Photos/Raw",
                help="Absolute path to the folder containing your input images"
            )
        with col_out:
            output_dir_str = st.text_input(
                "Output Folder Path",
                placeholder="Windows: C:\\Photos\\Output  |  Mac: /Users/name/Photos/Output",
                help="Absolute path where 'transparent' and 'white_background' subfolders will be created"
            )

        overlap_warning = False
        if input_dir_str.strip() and output_dir_str.strip():
            if check_path_overlap(input_dir_str.strip(), output_dir_str.strip()):
                overlap_warning = True
                st.warning("⚠️ **Directory Conflict**: Input and Output folders are identical or nested inside each other. Please select distinct folders.")

        image_files = []
        if input_dir_str.strip():
            input_p = Path(input_dir_str.strip()).expanduser()
            if input_p.exists() and input_p.is_dir():
                image_files = scan_images(str(input_p))
                st.info(f"🔍 Found **{len(image_files):,}** supported images (JPG, PNG, WEBP) in `{input_p}`")
            else:
                st.caption("ℹ️ Please enter an existing directory path.")

        # Real-time Stats Cards
        out_base_cand = Path(output_dir_str.strip()).expanduser() if output_dir_str.strip() else None
        prior_completed = 0
        if out_base_cand and out_base_cand.exists():
            tr = BatchProgressTracker(out_base_cand)
            prior_completed = len([f for f in image_files if tr.is_processed(f.name)])

        st.markdown(f"""
        <div class="metric-grid">
            <div class="stat-card">
                <div class="stat-val">{len(image_files):,}</div>
                <div class="stat-label">Total Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{prior_completed:,}</div>
                <div class="stat-label">Previously Done</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{max(0, len(image_files) - prior_completed):,}</div>
                <div class="stat-label">Remaining</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(st.session_state.recent_errors)}</div>
                <div class="stat-label">Failures</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Batch Action Controls (Start / Resume / Cancel / Open Folder)
        col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 3])
        with col_btn1:
            btn_label = "▶️ Resume Batch" if prior_completed > 0 and prior_completed < len(image_files) else "🚀 Start Batch"
            start_btn = st.button(
                btn_label,
                type="primary",
                disabled=st.session_state.is_running or len(image_files) == 0 or overlap_warning
            )
        with col_btn2:
            cancel_btn = st.button("🛑 Cancel", disabled=not st.session_state.is_running)
        with col_btn3:
            if output_dir_str.strip() and Path(output_dir_str.strip()).expanduser().exists():
                if st.button("📂 Open Output Directory in Explorer/Finder"):
                    open_folder_in_os(Path(output_dir_str.strip()).expanduser())

        if cancel_btn:
            st.session_state.cancel_requested = True
            st.warning("Cancellation requested. Safe stop after current image finishes...")

        # Progress and Telemetry Container
        telemetry_area = st.empty()
        preview_area = st.container()

        # Error Details Expander
        if st.session_state.recent_errors:
            with st.expander(f"⚠️ View Error Log ({len(st.session_state.recent_errors)} items)", expanded=False):
                for err_item in st.session_state.recent_errors:
                    st.error(err_item)

        if start_btn:
            out_base = Path(output_dir_str.strip()).expanduser().resolve()
            out_base.mkdir(parents=True, exist_ok=True)

            lock = DirectoryLock(out_base)
            if not lock.acquire():
                st.error("🔒 **Directory Locked**: Another batch worker is actively writing to this directory. Wait for it to finish or choose a separate folder.")
                return

            st.session_state.is_running = True
            st.session_state.cancel_requested = False
            st.session_state.batch_summary = None
            st.session_state.recent_errors = []

            trans_dir = out_base / "transparent"
            white_dir = out_base / "white_background"

            if export_format in ("transparent", "both"):
                trans_dir.mkdir(parents=True, exist_ok=True)
            if export_format in ("white", "both"):
                white_dir.mkdir(parents=True, exist_ok=True)

            logger = setup_logger(out_base / "batch_errors.log")

            current_settings = {
                "canvas_dim": canvas_dim,
                "padding_pct": padding_pct,
                "export_format": export_format,
                "jpg_quality": jpg_quality
            }
            tracker = BatchProgressTracker(out_base, current_settings=current_settings)

            session = get_cached_session(device_choice)

            # Filter items for resumption
            items_to_process = []
            for f in image_files:
                if skip_completed and tracker.is_processed(f.name):
                    continue
                items_to_process.append(f)

            total_items = len(items_to_process)
            completed_count = 0
            failed_count = 0
            skipped_count = len(image_files) - total_items

            start_time = time.time()
            durations = []

            try:
                for idx, img_path in enumerate(items_to_process):
                    if st.session_state.cancel_requested:
                        logger.info("Batch safely stopped by user cancellation.")
                        st.warning(f"Batch cancelled. Safely stopped after {completed_count} images.")
                        break

                    item_start = time.time()
                    current_filename = img_path.name
                    elapsed = time.time() - start_time
                    
                    # Calculate ETA when at least 2 items processed
                    if len(durations) >= 2:
                        avg_sec_per_item = sum(durations[-5:]) / len(durations[-5:])
                        remaining_items = total_items - idx
                        eta_str = format_duration(avg_sec_per_item * remaining_items)
                    else:
                        eta_str = "Calculating..."

                    elapsed_str = format_duration(elapsed)
                    pct = idx / max(total_items, 1)

                    with telemetry_area.container():
                        st.progress(pct, text=f"Processing [{idx + 1}/{total_items}] • {current_filename}")
                        c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                        c_t1.caption(f"⏱️ **Elapsed**: {elapsed_str}")
                        c_t2.caption(f"⏳ **Est. Remaining**: {eta_str}")
                        c_t3.caption(f"✅ **Processed**: {completed_count}")
                        c_t4.caption(f"❌ **Failed**: {failed_count}")

                    try:
                        # Process image non-destructively
                        result = process_image(
                            input_path_or_bytes=str(img_path),
                            rembg_session=session,
                            canvas_size=(canvas_dim, canvas_dim),
                            padding_percent=padding_pct,
                            export_format=export_format,
                            jpg_quality=jpg_quality
                        )

                        stem = img_path.stem
                        if result["transparent"] is not None:
                            out_png = trans_dir / f"{stem}.png"
                            result["transparent"].save(out_png, format="PNG", optimize=True)

                        if result["white"] is not None:
                            out_jpg = white_dir / f"{stem}.jpg"
                            result["white"].save(out_jpg, format="JPEG", quality=jpg_quality)

                        tracker.record_success(current_filename)
                        completed_count += 1
                        durations.append(time.time() - item_start)

                        # Update preview
                        with preview_area:
                            c_orig, c_trans, c_white = st.columns(3)
                            with c_orig:
                                st.caption(f"Original: {current_filename}")
                                st.image(str(img_path), use_container_width=True)
                            with c_trans:
                                st.caption("Centered Transparent PNG")
                                if result["transparent"] is not None:
                                    st.image(result["transparent"], use_container_width=True)
                            with c_white:
                                st.caption("Centered White Canvas JPG")
                                if result["white"] is not None:
                                    st.image(result["white"], use_container_width=True)

                    except Exception as err:
                        failed_count += 1
                        tracker.record_failure(current_filename)
                        err_line = f"Failed on '{current_filename}': {str(err)}"
                        st.session_state.recent_errors.append(err_line)
                        logger.error(err_line)

            finally:
                lock.release()

            st.session_state.is_running = False
            total_elapsed = round(time.time() - start_time, 2)
            telemetry_area.success(f"🎉 Batch execution finished in {format_duration(total_elapsed)}!")

            st.session_state.batch_summary = {
                "total_scanned": len(image_files),
                "processed": completed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "elapsed": format_duration(total_elapsed),
                "output_dir": str(out_base)
            }

        # Show Batch Summary
        if st.session_state.batch_summary:
            summary = st.session_state.batch_summary
            st.success("🎉 **Batch Process Completed!**")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Scanned", summary["total_scanned"])
            m2.metric("Processed", summary["processed"])
            m3.metric("Skipped", summary["skipped"])
            m4.metric("Failures", summary["failed"])
            m5.metric("Total Time", summary["elapsed"])
            st.info(f"📂 Results saved to: `{summary['output_dir']}`")

    # -------------------------------------------------------------
    # TAB 2: Multi-File Upload Mode (For quick batches & ZIP download)
    # -------------------------------------------------------------
    with tab_upload:
        st.write("Upload images directly from your browser to process and download as a ZIP file.")
        uploaded_files = st.file_uploader(
            "Select images to remove background",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.write(f"Selected **{len(uploaded_files)}** files.")
            if st.button("⚡ Process Uploaded Files", type="primary"):
                session = get_cached_session(device_choice)
                zip_buffer = io.BytesIO()
                
                upload_progress = st.progress(0, text="Processing files...")
                upload_preview = st.container()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for i, file_obj in enumerate(uploaded_files):
                        file_bytes = file_obj.read()
                        stem = Path(file_obj.name).stem

                        res = process_image(
                            input_path_or_bytes=io.BytesIO(file_bytes),
                            rembg_session=session,
                            canvas_size=(canvas_dim, canvas_dim),
                            padding_percent=padding_pct,
                            export_format=export_format,
                            jpg_quality=jpg_quality
                        )

                        if res["transparent"] is not None:
                            img_byte_arr = io.BytesIO()
                            res["transparent"].save(img_byte_arr, format="PNG")
                            zip_file.writestr(f"transparent/{stem}.png", img_byte_arr.getvalue())

                        if res["white"] is not None:
                            img_byte_arr = io.BytesIO()
                            res["white"].save(img_byte_arr, format="JPEG", quality=jpg_quality)
                            zip_file.writestr(f"white_background/{stem}.jpg", img_byte_arr.getvalue())

                        upload_progress.progress((i + 1) / len(uploaded_files), text=f"Processed {file_obj.name}")

                        # Preview first 3 images
                        if i < 3:
                            with upload_preview:
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.caption(f"Original: {file_obj.name}")
                                    st.image(file_bytes, use_container_width=True)
                                with c2:
                                    st.caption("Transparent PNG")
                                    if res["transparent"]:
                                        st.image(res["transparent"], use_container_width=True)
                                with c3:
                                    st.caption("White JPG")
                                    if res["white"]:
                                        st.image(res["white"], use_container_width=True)

                zip_buffer.seek(0)
                st.success("✅ Upload batch processing completed!")
                st.download_button(
                    label="📦 Download Results as ZIP",
                    data=zip_buffer,
                    file_name="processed_product_photos.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()

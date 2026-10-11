import streamlit as st
import cv2
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from PIL import Image

# Import internal modules
from config import (
    SPECIES_LIST,
    RISK_LEVELS,
    DEFAULT_CONFIDENCE,
    SNAPSHOTS_DIR,
    SAMPLES_DIR,
    DATA_DIR
)
from database.db import db
from detector.camera_stream import CameraStream
from detector.yolo_detector import YOLOWildlifeDetector
from detector.tracker import AnimalTracker
from detector.species_meta import SPECIES_METADATA, get_species_info
from alert_system.notifier import notifier

# Page Configuration
st.set_page_config(
    page_title="AI Wildlife Camera - 10 Species Detection",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1b4332;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #2d6a4f;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .alert-critical {
        background-color: #ffe5e5;
        border: 2px solid #ff4d4d;
        color: #900;
        padding: 12px 18px;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Plains_Zebra_Equus_quagga.jpg/320px-Plains_Zebra_Equus_quagga.jpg", use_container_width=True)
st.sidebar.title("🐾 AI Camera Controls")

# Camera Source Selection
cam_source_type = st.sidebar.selectbox(
    "Camera Source",
    options=["Simulator / Wildlife Clips", "Webcam (Index 0)", "Custom Video File / RTSP"],
    index=0
)

custom_uri = "0"
if cam_source_type == "Webcam (Index 0)":
    custom_uri = "0"
elif cam_source_type == "Simulator / Wildlife Clips":
    custom_uri = "sample.mp4"
else:
    custom_uri = st.sidebar.text_input("Enter RTSP URL or Video Path", value="0")

conf_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.10,
    max_value=1.00,
    value=DEFAULT_CONFIDENCE,
    step=0.05
)

enable_audio = st.sidebar.checkbox("Enable Audio Siren", value=True)
notifier.enable_sound = enable_audio

st.sidebar.divider()
st.sidebar.subheader("🛠️ Database Utilities")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.button("🌱 Seed DB", help="Add 120 historical sightings"):
        from scripts.seed_database import seed_sample_sightings
        seed_sample_sightings(120)
        st.sidebar.success("Database Seeded!")
        time.sleep(1)
        st.rerun()

with col_s2:
    if st.button("📥 Get Samples", help="Download sample wildlife photos"):
        from scripts.download_samples import download_or_generate_samples
        download_or_generate_samples()
        st.sidebar.success("Samples Ready!")
        time.sleep(1)
        st.rerun()

# Header
st.markdown('<div class="main-header">🐾 10 Wildlife Animal Detection Using AI Camera</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-Time Computer Vision & Surveillance: Elephant • Tiger • Lion • Leopard • Bear • Deer • Giraffe • Zebra • Wolf • Rhinoceros</div>', unsafe_allow_html=True)

# Tabs
tab_live, tab_analytics, tab_logs, tab_gallery, tab_guide = st.tabs([
    "🎥 Live AI Camera",
    "📊 Analytics & Insights",
    "📋 Sightings Database",
    "🖼️ Snapshot Gallery",
    "📚 10 Species Profile"
])

# ----------------- TAB 1: LIVE AI CAMERA -----------------
with tab_live:
    col_video, col_alerts = st.columns([7, 3])

    with col_alerts:
        st.subheader("🚨 Active Alerts")
        active_alerts = db.get_recent_alerts(limit=5, unresolved_only=True)
        if active_alerts:
            for alt in active_alerts:
                st.markdown(
                    f"""<div class="alert-critical">
                        <strong>⚠️ {alt['alert_type']}</strong><br/>
                        {alt['message']}<br/>
                        <small>Time: {alt['timestamp']}</small>
                    </div>""",
                    unsafe_allow_html=True
                )
                if st.button(f"Resolve Alert #{alt['id']}", key=f"res_{alt['id']}"):
                    db.resolve_alert(alt['id'])
                    st.rerun()
        else:
            st.success("✅ No active predator or danger alerts. Perimeter secure.")

        st.divider()
        st.subheader("🎯 Monitored Species")
        st.caption("10 Target Species Detection Status")
        for i in range(0, len(SPECIES_LIST), 2):
            s1 = SPECIES_LIST[i]
            s2 = SPECIES_LIST[i+1] if i+1 < len(SPECIES_LIST) else ""
            c1, c2 = st.columns(2)
            info1 = get_species_info(s1)
            c1.markdown(f"{info1['icon']} **{s1}**")
            if s2:
                info2 = get_species_info(s2)
                c2.markdown(f"{info2['icon']} **{s2}**")

    with col_video:
        st.subheader("📹 Real-Time Detection Feed")
        stream_placeholder = st.empty()
        status_placeholder = st.empty()

        run_camera = st.checkbox("▶️ Start Live Camera Feed", value=False)

        if run_camera:
            camera = CameraStream(source=custom_uri)
            detector = YOLOWildlifeDetector(conf_thresh=conf_threshold)
            tracker = AnimalTracker()

            frame_counter = 0
            start_time = time.time()

            # Live Loop
            stop_btn = st.button("⏹️ Stop Camera Feed")
            while run_camera and not stop_btn:
                ret, frame = camera.read_frame()
                if not ret or frame is None:
                    status_placeholder.warning("Camera stream interrupted or ended.")
                    break

                frame_counter += 1
                fps = frame_counter / max(1e-5, (time.time() - start_time))

                # Detection & Tracking
                raw_dets = detector.detect(frame, conf_threshold=conf_threshold)
                tracked_animals = tracker.update(raw_dets)

                # Database Logging
                for track in tracked_animals:
                    if track.should_log_to_db():
                        sp_name = track.animal_name
                        conf = track.confidence
                        risk = RISK_LEVELS.get(sp_name, "LOW")

                        # Save snapshot
                        ts_str = time.strftime("%Y%m%d_%H%M%S")
                        snap_name = f"{sp_name.lower()}_track{track.track_id}_{ts_str}.jpg"
                        snap_path = SNAPSHOTS_DIR / snap_name
                        x1, y1, x2, y2 = track.bbox
                        h, w = frame.shape[:2]
                        crop = frame[max(0, y1-10):min(h, y2+10), max(0, x1-10):min(w, x2+10)]
                        if crop.size > 0:
                            cv2.imwrite(str(snap_path), crop)
                            rel_snap = f"snapshots/{snap_name}"
                        else:
                            rel_snap = None

                        db.log_detection(
                            animal_name=sp_name,
                            confidence=conf,
                            bbox=track.bbox,
                            track_id=track.track_id,
                            camera_id=1,
                            snapshot_path=rel_snap
                        )

                        if risk in ["CRITICAL", "HIGH"]:
                            notifier.trigger_alert(sp_name, risk, camera_id=1, confidence=conf)

                # Render overlays
                annotated = detector.draw_overlays(frame, tracked_animals)
                rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                stream_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)
                status_placeholder.info(f"⚡ Camera Active | FPS: {fps:.1f} | Active Animals In View: {len(tracked_animals)}")
                time.sleep(0.04)

            camera.release()
        else:
            # Display standby preview
            sample_preview = SAMPLES_DIR / "elephant.jpg"
            if sample_preview.exists():
                stream_placeholder.image(str(sample_preview), caption="Standby Camera Preview (Check 'Start Live Camera Feed' above to begin)", use_container_width=True)
            else:
                stream_placeholder.info("Click 'Start Live Camera Feed' above to activate surveillance.")

# ----------------- TAB 2: ANALYTICS & INSIGHTS -----------------
with tab_analytics:
    stats = db.get_summary_statistics()

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Sightings", stats["total_detections"])
    m2.metric("Species Identified", f"{stats['unique_species']} / 10")
    m3.metric("Unresolved Alerts", stats["active_alerts"])
    m4.metric("Active Cameras", stats["active_cameras"])

    st.divider()

    # Visual Charts
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📊 Sightings by Species")
        if stats["species_counts"]:
            df_sp = pd.DataFrame(stats["species_counts"])
            fig_bar = px.bar(
                df_sp,
                x="animal_name",
                y="count",
                color="animal_name",
                text="count",
                labels={"animal_name": "Wildlife Species", "count": "Sightings Count"},
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_bar.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No sightings logged yet. Use 'Seed DB' in sidebar to load demonstration data.")

    with col_chart2:
        st.subheader("⚠️ Threat & Risk Distribution")
        if stats["risk_counts"]:
            df_risk = pd.DataFrame(stats["risk_counts"])
            color_map = {
                "CRITICAL": "#e74c3c",
                "HIGH": "#e67e22",
                "MEDIUM": "#f1c40f",
                "LOW": "#2ecc71"
            }
            fig_pie = px.pie(
                df_risk,
                names="risk_level",
                values="count",
                hole=0.45,
                color="risk_level",
                color_discrete_map=color_map
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No risk records logged yet.")

    st.subheader("🕒 Sighting Frequency by Hour of Day (24-Hour Timeline)")
    if stats["hourly_counts"]:
        df_hour = pd.DataFrame(stats["hourly_counts"])
        # Format hours as 00:00 - 23:00
        df_hour["hour_label"] = df_hour["hour"].apply(lambda h: f"{int(h):02d}:00")
        fig_line = px.line(
            df_hour,
            x="hour_label",
            y="count",
            markers=True,
            labels={"hour_label": "Time of Day", "count": "Sightings Count"},
            line_shape="spline"
        )
        fig_line.update_traces(line_color="#2d6a4f", line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No hourly timeline data available yet.")

# ----------------- TAB 3: SIGHTINGS DATABASE -----------------
with tab_logs:
    st.subheader("📋 Wildlife Sighting Log & Filter")

    f_col1, f_col2, f_col3 = st.columns([3, 3, 2])
    with f_col1:
        sel_species = st.selectbox("Filter by Species", options=["All"] + SPECIES_LIST)
    with f_col2:
        sel_conf = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.05)
    with f_col3:
        row_limit = st.selectbox("Max Rows", [25, 50, 100, 200], index=1)

    records = db.get_recent_detections(limit=row_limit, animal_filter=sel_species, min_confidence=sel_conf)

    if records:
        df_records = pd.DataFrame(records)
        st.dataframe(
            df_records[["id", "timestamp", "animal_name", "confidence", "risk_level", "track_id", "camera_name"]],
            use_container_width=True,
            column_config={
                "id": "Log ID",
                "timestamp": "Timestamp",
                "animal_name": "Animal",
                "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.2f"),
                "risk_level": "Threat Level",
                "track_id": "Track ID",
                "camera_name": "Camera Location"
            }
        )

        # CSV Export
        csv_data = df_records.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Sightings to CSV",
            data=csv_data,
            file_name=f"wildlife_sightings_{time.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No records matched the selected filters.")

# ----------------- TAB 4: SNAPSHOT GALLERY -----------------
with tab_gallery:
    st.subheader("🖼️ Wildlife Photographic Evidence Gallery")
    snapshots = sorted(list(SNAPSHOTS_DIR.glob("*.jpg")) + list(SNAPSHOTS_DIR.glob("*.png")), key=lambda p: p.stat().st_mtime, reverse=True)

    if snapshots:
        cols_per_row = 4
        cols = st.columns(cols_per_row)
        for idx, snap_path in enumerate(snapshots[:20]):
            with cols[idx % cols_per_row]:
                try:
                    img = Image.open(snap_path)
                    st.image(img, caption=snap_path.stem.replace("_", " ").title(), use_container_width=True)
                except Exception as e:
                    st.caption(f"Error loading {snap_path.name}")
    else:
        st.info("No snapshots recorded yet. Run live detection or click 'Get Samples' in the sidebar to download sample evidence.")

# ----------------- TAB 5: 10 SPECIES PROFILES -----------------
with tab_guide:
    st.subheader("📚 10 Target Wildlife Species Reference Guide")

    for animal in SPECIES_LIST:
        info = get_species_info(animal)
        with st.expander(f"{info['icon']} {animal.upper()} — {info['scientific_name']} [{info['risk_level']} RISK]"):
            col_info1, col_info2 = st.columns([1, 2])
            with col_info1:
                sample_img_path = SAMPLES_DIR / f"{animal.lower()}.jpg"
                if sample_img_path.exists():
                    st.image(str(sample_img_path), use_container_width=True)
                else:
                    st.markdown(f"**Icon:** {info['icon']}")
            with col_info2:
                st.markdown(f"**Classification:** {info['category']}")
                st.markdown(f"**Conservation Status:** `{info['conservation_status']}`")
                st.markdown(f"**Threat Level:** `{info['risk_level']}`")
                st.markdown(f"**Behavioral Risk:** {info['danger_reason']}")
                st.markdown(f"**Ranger / Community Protocol:** {info['safety_advice']}")

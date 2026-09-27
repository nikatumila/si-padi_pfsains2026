import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# ==============================================================================
# 1. KONFIGURASI HALAMAN INDUSTRIAL DARK
# ==============================================================================
st.set_page_config(
    page_title="SI-PADI — Telemetri & Pusat Kendali IoT",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0f1015;
        color: #e2e4e9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(180deg, #181b24 0%, #13151c 100%);
        border: 1px solid #282d3c;
        border-radius: 10px;
        padding: 18px 24px;
        margin-bottom: 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
    }
    .navbar-title {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.3px;
        color: #f1f3f7;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .navbar-sub {
        font-size: 13px;
        color: #9299a8;
        margin-top: 4px;
        font-weight: 400;
    }
    .clock-badge {
        background-color: #1a1e29;
        border: 1px solid #333a4d;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 14px;
        color: #d19a38;
        font-family: monospace;
        font-weight: 600;
    }
    .summary-card {
        background: #141720;
        border: 1px solid #232838;
        border-radius: 8px;
        padding: 16px 20px;
        height: 100%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .summary-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #8890a1;
        margin-bottom: 8px;
    }
    .summary-metric {
        font-size: 34px;
        font-weight: 700;
        color: #d19a38;
        line-height: 1.1;
    }
    .summary-unit {
        font-size: 18px;
        font-weight: 400;
        color: #8890a1;
    }
    .summary-subtext {
        font-size: 12px;
        color: #697184;
        margin-top: 6px;
    }
    .chamber-card {
        background-color: #141720;
        border: 1px solid #232838;
        border-radius: 8px;
        padding: 16px;
        height: 100%;
    }
    .chamber-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #202534;
        padding-bottom: 10px;
        margin-bottom: 12px;
    }
    .chamber-name {
        font-size: 16px;
        font-weight: 700;
        color: #f1f3f7;
    }
    .status-pill-active {
        background-color: #2b2111;
        color: #e5a43b;
        border: 1px solid #543f1e;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .status-pill-done {
        background-color: #12281a;
        color: #3fb950;
        border: 1px solid #238636;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .param-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 4px 0;
        font-size: 13px;
        color: #8890a1;
    }
    .param-val {
        font-size: 16px;
        font-weight: 700;
        color: #f1f3f7;
    }
    .control-panel-box {
        background: #141720;
        border: 1px solid #282e3f;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .control-panel-heading {
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        color: #d19a38;
        border-bottom: 1px solid #202534;
        padding-bottom: 8px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. INISIALISASI SESI: 1 UNIT PENGERING 1 TON (3 ZONA RAK)
# ==============================================================================
if 'initialized' not in st.session_state:
    st.session_state.detik_berjalan = 0
    st.session_state.cuaca = "☀️ Surya Penuh (Suplai PLTS Penuh)"
    st.session_state.mode_operasi = "Otomatis (Closed-Loop PID)"
    st.session_state.auto_play = False
    st.session_state.blower_induk = True
    st.session_state.pemanas_induk = True
    st.session_state.target_ka_global = 14.0
    st.session_state.target_suhu_global = 42

    st.session_state.zona_data = {
        "Zona 1 (Rak Atas)": {
            "suhu": 40.7,
            "target_suhu": 42,
            "ka": 25.7,
            "status": "Proses",
            "history": [{"Menit": 0, "Suhu": 40.7, "Kadar Air": 25.7}]
        },
        "Zona 2 (Rak Tengah)": {
            "suhu": 45.1,
            "target_suhu": 45,
            "ka": 17.9,
            "status": "Proses",
            "history": [{"Menit": 0, "Suhu": 45.1, "Kadar Air": 17.9}]
        },
        "Zona 3 (Rak Bawah)": {
            "suhu": 41.3,
            "target_suhu": 40,
            "ka": 26.4,
            "status": "Proses",
            "history": [{"Menit": 0, "Suhu": 41.3, "Kadar Air": 26.4}]
        }
    }
    st.session_state.initialized = True

# ==============================================================================
# 3. SIDEBAR SIMULASI DINAMIKA SISTEM
# ==============================================================================
st.sidebar.markdown("### 🎛️ Konsol Demo 5 Menit")
st.sidebar.caption("Simulasi 5 menit setara siklus pengeringan 1 ton 24 jam")

auto_toggle = st.sidebar.toggle("▶️ Jalankan Simulasi Otomatis", value=st.session_state.auto_play)
st.session_state.auto_play = auto_toggle

detik_maks = 300  # 5 Menit
prog = min(1.0, st.session_state.detik_berjalan / detik_maks)
st.sidebar.progress(prog, text=f"Waktu Presentasi: {st.session_state.detik_berjalan // 60:02d}:{st.session_state.detik_berjalan % 60:02d} / 05:00")

col_btn_a, col_btn_b = st.sidebar.columns(2)
with col_btn_a:
    if st.sidebar.button("⏩ +30 Detik", use_container_width=True):
        st.session_state.detik_berjalan = min(detik_maks, st.session_state.detik_berjalan + 30)
with col_btn_b:
    if st.sidebar.button("🔄 Reset Demo", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⛅ Sumber Pasokan Energi Primer")
pilihan_cuaca = st.sidebar.selectbox(
    "Status Radiasi PLTS:",
    [
        "☀️ Surya Penuh (Suplai PLTS Penuh)", 
        "☁️ Berawan (Hibrida PLTS & Biomassa)", 
        "🌧️ Hujan / Malam Hari (Biomassa Penuh)"
    ]
)
st.session_state.cuaca = pilihan_cuaca

def update_kondisi_zona(dt_detik):
    for z_nama, z in st.session_state.zona_data.items():
        if z["status"] == "Selesai":
            continue
        
        if "Rak Tengah" in z_nama:
            laju = (3.9 / 90) * dt_detik
        elif "Rak Atas" in z_nama:
            laju = (11.7 / 210) * dt_detik
        else:
            laju = (12.4 / 270) * dt_detik

        if st.session_state.blower_induk and st.session_state.pemanas_induk:
            z["ka"] = max(float(st.session_state.target_ka_global), round(z["ka"] - laju, 1))
        
        if z["ka"] <= st.session_state.target_ka_global:
            z["status"] = "Selesai"

        z["suhu"] = round(z["target_suhu"] + np.random.uniform(-0.4, 0.4), 1)

        z["history"].append({
            "Menit": round(st.session_state.detik_berjalan / 60, 1),
            "Suhu": z["suhu"],
            "Kadar Air": z["ka"]
        })

# ==============================================================================
# 4. HEADER UTAMA
# ==============================================================================
waktu_server = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div class="top-navbar">
    <div>
        <div class="navbar-title">🌾 SI-PADI — Panel Monitoring Pengering Gabah Padi</div>
        <div class="navbar-sub">Unit Pengering Tunggal Kapasitas 1 Ton · 3 Zona Sensor Rak Vertikal · Mitra: PUSAKA BLORA</div>
    </div>
    <div style="display:flex; align-items:center; gap:14px;">
        <span style="font-size:12px; color:{'#3fb950' if st.session_state.auto_play else '#d19a38'}; font-weight:600;">
            {'● DEMO AUTO-RUN AKTIF' if st.session_state.auto_play else '⏸️ SIMULASI STANDBY'}
        </span>
        <div class="clock-badge">{waktu_server} WIB</div>
    </div>
</div>
""", unsafe_allow_html=True)

list_ka = [z["ka"] for z in st.session_state.zona_data.values()]
rata_ka = round(sum(list_ka) / len(list_ka), 1)
total_selesai = sum(1 for z in st.session_state.zona_data.values() if z["status"] == "Selesai")

sisa_detik = max(0, detik_maks - st.session_state.detik_berjalan)
est_menit_demo = sisa_detik // 60
est_detik_demo = sisa_detik % 60

# ==============================================================================
# 5. TAB NAVIGASI SISTEM
# ==============================================================================
tab_dashboard, tab_hmi, tab_spek = st.tabs([
    "📊 Panel Operasional 1 Unit (3 Zona Rak)", 
    "🔄 Diagram Alir Sistem (3D Isometrik HMI)", 
    "📑 Spesifikasi Desain & Rencana Anggaran (RAB)"
])

# ------------------------------------------------------------------------------
# TAB 1: DASHBOARD OPERASIONAL
# ------------------------------------------------------------------------------
with tab_dashboard:
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Rata-Rata Kadar Air Batch 1 Ton</div>
            <div class="summary-metric">{rata_ka:.1f} <span class="summary-unit">%</span></div>
            <div class="summary-subtext">Standar Target Akhir SNI 6128:2020: {st.session_state.target_ka_global:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Keseragaman Dehidrasi Rak</div>
            <div class="summary-metric">{total_selesai} <span class="summary-unit">/ 3 Zona Selesai</span></div>
            <div class="summary-subtext">{"Proses dehidrasi berlangsung merata" if total_selesai < 3 else "Seluruh lapisan muatan telah memenuhi standar simpan"}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Estimasi Sisa Durasi Siklus</div>
            <div class="summary-metric">{est_menit_demo:02d} <span class="summary-unit">mnt</span> {est_detik_demo:02d} <span class="summary-unit">dtk</span></div>
            <div class="summary-subtext">Waktu demo real-time 5 menit setara pengeringan 24 jam</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    col_workspace_l, col_workspace_r = st.columns([2.2, 1.0])

    with col_workspace_l:
        st.markdown("##### Telemetri 3 Titik Sensor Rak Gabah (1 Unit Ruang Pengering)")
        zona_fokus = st.radio(
            "Pilih Titik Ketinggian Rak untuk Analitik & Monitoring Grafik:",
            ["Zona 1 (Rak Atas)", "Zona 2 (Rak Tengah)", "Zona 3 (Rak Bawah)"],
            horizontal=True
        )

        col_z1, col_z2, col_z3 = st.columns(3)
        slot_kolom = {
            "Zona 1 (Rak Atas)": col_z1, 
            "Zona 2 (Rak Tengah)": col_z2, 
            "Zona 3 (Rak Bawah)": col_z3
        }

        for nama_z, slot in slot_kolom.items():
            dt_z = st.session_state.zona_data[nama_z]
            badge_tipe = "status-pill-done" if dt_z["status"] == "Selesai" else "status-pill-active"
            border_fokus = "border: 1.5px solid #d19a38; box-shadow: 0 0 10px rgba(209,154,56,0.25);" if nama_z == zona_fokus else ""

            with slot:
                st.markdown(f"""
                <div class="chamber-card" style="{border_fokus}">
                    <div class="chamber-header">
                        <span class="chamber-name">{nama_z}</span>
                        <span class="{badge_tipe}">{dt_z["status"]}</span>
                    </div>
                    <div class="param-row">
                        <span>Suhu Termal Terukur:</span>
                        <span class="param-val">{dt_z['suhu']:.1f} °C</span>
                    </div>
                    <div class="param-row">
                        <span>Target Setpoint:</span>
                        <span>{dt_z['target_suhu']} °C</span>
                    </div>
                    <div class="param-row" style="margin-top:4px;">
                        <span>Kadar Air Aktual:</span>
                        <span class="param-val" style="color:{'#3fb950' if dt_z['status'] == 'Selesai' else '#d19a38'};">{dt_z['ka']:.1f} %</span>
                    </div>
                    <div class="param-row">
                        <span>Batas Aman SNI:</span>
                        <span>{st.session_state.target_ka_global:.1f} %</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:14px; padding-top:8px; border-top:1px solid #1f2431; font-size:11px;">
                        <span style="color:{'#3fb950' if st.session_state.blower_induk else '#697184'}; font-weight:600;">
                            🌀 BLOWER: {'ON' if st.session_state.blower_induk else 'OFF'}
                        </span>
                        <span style="color:{'#e5a43b' if st.session_state.pemanas_induk else '#697184'}; font-weight:600;">
                            🔥 PEMANAS: {'ON' if st.session_state.pemanas_induk else 'OFF'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

        zona_aktif = st.session_state.zona_data[zona_fokus]
        st.markdown(f"""
        <div class="summary-card" style="margin-bottom: 10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:15px; font-weight:700; color:#f1f3f7;">Grafik Dinamika Kinetika — {zona_fokus}</span>
                    <div style="font-size:12px; color:#8890a1; margin-top:2px;">Profil Suhu Termal (°C) terhadap Dehidrasi Kadar Air (%) Gabah 1 Ton</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:11px; color:#8890a1;">Durasi Simulasi</div>
                    <div style="font-size:18px; font-weight:700; color:#f1f3f7;">{st.session_state.detik_berjalan // 60:02d}:{st.session_state.detik_berjalan % 60:02d} <span style="font-size:12px; font-weight:normal; color:#8890a1;">Menit</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_telemetri = pd.DataFrame(zona_aktif["history"]).set_index("Menit")
        st.line_chart(df_telemetri[["Suhu", "Kadar Air"]], color=["#d19a38", "#3fb950"])

    with col_workspace_r:
        st.markdown(f"""
        <div class="control-panel-box">
            <div class="control-panel-heading">Pusat Kendali Unit 1 Ton</div>
        """, unsafe_allow_html=True)

        st.session_state.target_ka_global = st.slider(
            "Target Akhir Kadar Air (SNI %):", 
            min_value=11.0, 
            max_value=16.0, 
            value=float(st.session_state.target_ka_global), 
            step=0.5
        )
        st.session_state.target_suhu_global = st.slider(
            "Setpoint Suhu Ruang Pengering (°C):", 
            min_value=35, 
            max_value=60, 
            value=int(st.session_state.target_suhu_global), 
            step=1
        )

        st.markdown("<div style='font-size:12px; font-weight:600; color:#8890a1; margin-top:14px; margin-bottom:8px;'>Kendali Aktuator Induk (1 Unit):</div>", unsafe_allow_html=True)
        col_sw1, col_sw2 = st.columns(2)
        with col_sw1:
            st.session_state.blower_induk = st.toggle("Blower Udara", value=st.session_state.blower_induk)
        with col_sw2:
            st.session_state.pemanas_induk = st.toggle("Elemen Pemanas", value=st.session_state.pemanas_induk)

        mode_terpilih = st.selectbox("Algoritma Pengendalian:", ["Otomatis (Closed-Loop PID)", "Manual Override System"])
        st.session_state.mode_operasi = mode_terpilih

        st.markdown(f"""
            <div style="font-size:12px; color:#8890a1; margin-top:14px; padding-top:10px; border-top:1px solid #202534;">
                Status Operasi: <strong style="color:#d19a38;">{mode_terpilih.split()[0]}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="📥 Ekspor Data Log Batch 1 Ton (.CSV)",
            data=df_telemetri.to_csv().encode('utf-8'),
            file_name=f"log_batch_1ton_sipadi.csv",
            mime="text/csv",
            use_container_width=True
        )

# ------------------------------------------------------------------------------
# TAB 2: HMI DIGITAL TWIN (1 UNIT RUMAH PENGERING - 3 TINGKAT RAK)
# ------------------------------------------------------------------------------
with tab_hmi:
    st.markdown("### 🗺️ Skema Integrasi Termal & Pembangkit EBT SI-PADI")
    st.caption("Visualisasi Terpadu Stasiun Bioenergi, Menara Penukar Panas (HE), 1 Unit Rumah Pengering Rak Bertingkat, dan PLTS 4.000 Wp[span_1](start_span)[span_1](end_span)")

    if "Surya" in st.session_state.cuaca:
        suplai_plts_wp = 3920
        status_baterai = 96.5
        suhu_ruang_bakar = 370
    elif "Berawan" in st.session_state.cuaca:
        suplai_plts_wp = 1850
        status_baterai = 78.0
        suhu_ruang_bakar = 415
    else:
        suplai_plts_wp = 0
        status_baterai = 54.0
        suhu_ruang_bakar = 460

    ka_z1 = st.session_state.zona_data["Zona 1 (Rak Atas)"]["ka"]
    ka_z2 = st.session_state.zona_data["Zona 2 (Rak Tengah)"]["ka"]
    ka_z3 = st.session_state.zona_data["Zona 3 (Rak Bawah)"]["ka"]

    svg_hmi_industrial = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1060 560" width="100%" height="100%" style="background-color: #12141c; border-radius: 10px; border: 1px solid #232838; font-family: -apple-system, sans-serif;">
      <defs>
        <marker id="arrow-amber" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#d19a38"/>
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#3fb950"/>
        </marker>
        <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#58a6ff"/>
        </marker>
      </defs>

      <!-- 1. STASIUN BIOENERGI & SISTEM PEMBERSIHAN GAS -->
      <rect x="20" y="20" width="670" height="520" rx="8" fill="#161822" stroke="#2b3246" stroke-width="1.5"/>
      <rect x="35" y="32" width="310" height="26" rx="4" fill="#202534"/>
      <text x="45" y="50" fill="#e2e4e9" font-size="12" font-weight="700" letter-spacing="0.5">1. STASIUN BIOENERGI &amp; GAS CLEANING</text>

      <path d="M 235 110 L 235 75 L 360 75" stroke="#3fb950" stroke-width="2.5" fill="none" marker-end="url(#arrow-green)"/>
      <text x="370" y="79" fill="#3fb950" font-size="10" font-weight="600">Aliran Emisi Bersih Terfiltrasi</text>

      <!-- Tungku Biomassa -->
      <rect x="40" y="170" width="130" height="200" rx="6" fill="#1d202d" stroke="#d19a38" stroke-width="2"/>
      <text x="105" y="205" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">TUNGKU BIOMASSA</text>
      <text x="105" y="225" fill="#8890a1" font-size="10" text-anchor="middle">Limbah Batang Padi</text>
      <rect x="52" y="245" width="106" height="55" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="105" y="280" fill="#ff7b72" font-size="18" font-weight="700" text-anchor="middle">{suhu_ruang_bakar} °C</text>
      <text x="105" y="340" fill="#8890a1" font-size="9" text-anchor="middle">Sensor Suhu Ruang Bakar</text>

      <path d="M 170 270 L 195 270" stroke="#d19a38" stroke-width="3" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- Heat Riser & Filter -->
      <rect x="195" y="110" width="80" height="260" rx="6" fill="#1a1d29" stroke="#8890a1" stroke-width="1.5"/>
      <text x="235" y="138" fill="#e2e4e9" font-size="10" font-weight="700" text-anchor="middle">HEAT RISER</text>
      <text x="235" y="153" fill="#8890a1" font-size="9" text-anchor="middle">(Cerobong)</text>
      <line x1="195" y1="175" x2="275" y2="175" stroke="#333a4d" stroke-width="2"/>
      <text x="235" y="210" fill="#d19a38" font-size="9" font-weight="600" text-anchor="middle">Filter Kasar</text>
      <line x1="195" y1="245" x2="275" y2="245" stroke="#333a4d" stroke-width="2"/>
      <text x="235" y="290" fill="#3fb950" font-size="9" font-weight="600" text-anchor="middle">HEPA &amp; VOC</text>
      <text x="235" y="305" fill="#3fb950" font-size="8" text-anchor="middle">Gas Filter</text>

      <path d="M 275 270 L 320 270" stroke="#d19a38" stroke-width="3" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- Heat Exchanger -->
      <rect x="320" y="110" width="145" height="260" rx="6" fill="#182026" stroke="#3fb950" stroke-width="2"/>
      <text x="392" y="138" fill="#3fb950" font-size="11" font-weight="700" text-anchor="middle">HEAT EXCHANGER</text>
      <text x="392" y="155" fill="#8890a1" font-size="9" text-anchor="middle">Penukar Kalor Hibrida</text>
      <circle cx="392" cy="205" r="28" fill="#0f1015" stroke="#3fb950" stroke-width="2"/>
      <text x="392" y="210" fill="#3fb950" font-size="13" font-weight="700" text-anchor="middle">85%</text>
      
      <rect x="332" y="250" width="121" height="42" rx="4" fill="#0f1015" stroke="#252d3a"/>
      <text x="392" y="267" fill="#58a6ff" font-size="9" font-weight="600" text-anchor="middle">Inlet Udara Bersih</text>
      <text x="392" y="282" fill="#e2e4e9" font-size="9" text-anchor="middle">Dipanaskan Bersih</text>
      <text x="392" y="340" fill="#8890a1" font-size="9" text-anchor="middle">Efisiensi Termal Optimal</text>

      <path d="M 465 270 L 510 270" stroke="#d19a38" stroke-width="3.5" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- 1 UNIT RUMAH PENGERING GABAH (3 TINGKAT RAK) -->
      <rect x="510" y="110" width="160" height="380" rx="6" fill="#1a1c24" stroke="#d19a38" stroke-width="2"/>
      <text x="590" y="138" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">RUMAH PENGERING</text>
      <text x="590" y="155" fill="#8890a1" font-size="9" text-anchor="middle">1 Unit (Dimensi 6x4x3m)</text>
      
      <!-- 3 Tingkat Rak Sensor -->
      <rect x="525" y="175" width="130" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="590" y="195" fill="#e2e4e9" font-size="10.5" font-weight="600" text-anchor="middle">Rak Atas (Zona 1)</text>
      <text x="590" y="213" fill="#d19a38" font-size="10.5" font-weight="700" text-anchor="middle">KA: {ka_z1:.1f}%</text>

      <rect x="525" y="235" width="130" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="590" y="255" fill="#e2e4e9" font-size="10.5" font-weight="600" text-anchor="middle">Rak Tengah (Zona 2)</text>
      <text x="590" y="273" fill="#d19a38" font-size="10.5" font-weight="700" text-anchor="middle">KA: {ka_z2:.1f}%</text>

      <rect x="525" y="295" width="130" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="590" y="315" fill="#e2e4e9" font-size="10.5" font-weight="600" text-anchor="middle">Rak Bawah (Zona 3)</text>
      <text x="590" y="333" fill="#d19a38" font-size="10.5" font-weight="700" text-anchor="middle">KA: {ka_z3:.1f}%</text>

      <text x="590" y="380" fill="#3fb950" font-size="10" font-weight="600" text-anchor="middle">Blower Udara Aktif</text>
      <text x="590" y="405" fill="#8890a1" font-size="9" text-anchor="middle">Kapasitas Batch Tunggal:</text>
      <text x="590" y="420" fill="#e2e4e9" font-size="10" font-weight="600" text-anchor="middle">1 Ton / Siklus</text>

      <!-- 2. SISTEM SURYA PLTS -->
      <rect x="710" y="20" width="330" height="520" rx="8" fill="#161822" stroke="#2b3246" stroke-width="1.5"/>
      <rect x="725" y="32" width="260" height="26" rx="4" fill="#202534"/>
      <text x="735" y="50" fill="#e2e4e9" font-size="12" font-weight="700" letter-spacing="0.5">2. SISTEM ENERGI SURYA (PLTS DARAT)</text>

      <rect x="730" y="80" width="290" height="110" rx="6" fill="#151d2a" stroke="#388bfd" stroke-width="2"/>
      <text x="875" y="118" fill="#58a6ff" font-size="12" font-weight="700" text-anchor="middle">ARRAY PANEL SURYA</text>
      <text x="875" y="145" fill="#e2e4e9" font-size="20" font-weight="700" text-anchor="middle">{suplai_plts_wp} Wp</text>
      <text x="875" y="168" fill="#8890a1" font-size="10" text-anchor="middle">Kapasitas Terpasang: 4.000 Wp Off-Grid</text>

      <path d="M 875 190 L 875 220" stroke="#58a6ff" stroke-width="2.5" fill="none" marker-end="url(#arrow-blue)"/>

      <rect x="755" y="220" width="240" height="60" rx="6" fill="#1d202d" stroke="#d19a38" stroke-width="1.5"/>
      <text x="875" y="244" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">SOLAR CHARGE CONTROLLER</text>
      <text x="875" y="264" fill="#3fb950" font-size="10" font-weight="600" text-anchor="middle">Efisiensi Pelacakan MPPT: 98%</text>

      <path d="M 875 280 L 875 310" stroke="#3fb950" stroke-width="2.5" fill="none" marker-end="url(#arrow-green)"/>

      <rect x="755" y="310" width="240" height="60" rx="6" fill="#1d202d" stroke="#3fb950" stroke-width="1.5"/>
      <text x="875" y="334" fill="#3fb950" font-size="11" font-weight="700" text-anchor="middle">BATERAI PENYIMPANAN</text>
      <text x="875" y="355" fill="#e2e4e9" font-size="13" font-weight="700" text-anchor="middle">{status_baterai:.1f}% Kapasitas Tersedia</text>

      <rect x="730" y="395" width="290" height="95" rx="6" fill="#0f1015" stroke="#2b3246"/>
      <text x="745" y="420" fill="#8890a1" font-size="10" font-weight="600">PENYALURAN DAYA OPERASIONAL:</text>
      <text x="745" y="443" fill="#e2e4e9" font-size="10.5">• Blower Sirkulasi Udara Termal (2x 500W)</text>
      <text x="745" y="465" fill="#e2e4e9" font-size="10.5">• Mikrokontroler IoT, Sensor &amp; Gateway Data</text>
    </svg>
    """
    st.components.v1.html(svg_hmi_industrial, height=580)

# ------------------------------------------------------------------------------
# TAB 3: SPESIFIKASI DESAIN & RAB
# ------------------------------------------------------------------------------
with tab_spek:
    st.markdown("### 📋 Spesifikasi Keteknikan & Rencana Anggaran Biaya Revisi")
    st.caption("Diselaraskan Penuh dengan Draf Final Usulan PFsains Pertamina Foundation 2026[span_2](start_span)[span_2](end_span)")

    col_spec_a, col_spec_b = st.columns(2)
    with col_spec_a:
        st.markdown("""
        **Parameter Teknis Unit SI-PADI:**[span_3](start_span)[span_3](end_span)
        * **Konfigurasi Unit:** 1 Unit Rumah Pengering Hibrida Tunggal (Dimensi ±6 m × 4 m × 3 m) berangka baja galvanis dengan insulasi polikarbonat[span_4](start_span)[span_4](end_span).
        * **Sistem Rak Pemantauan:** 3 Tingkat Rak Stainless Steel (Zona Atas, Tengah, dan Bawah) untuk menjamin keseragaman dehidrasi gabah[span_5](start_span)[span_5](end_span).
        * **Kapasitas Olah:** ±1 Ton gabah segar per siklus pengeringan (18–24 jam)[span_6](start_span)[span_6](end_span).
        * **Profil Kadar Air:** Diturunkan dari 27,72% (basis basah) menjadi ≤ 14,0% (Standar SNI 6128:2020)[span_7](start_span)[span_7](end_span).
        * **Sumber Daya:** Array PLTS 4.000 Wp baterai penyimpanan & tungku biomassa batang padi[span_8](start_span)[span_8](end_span).
        * **Tingkat Kesiapan Teknologi:** TKT level 6–7 (teruji operasional lapangan)[span_9](start_span)[span_9](end_span).
        """)

    with col_spec_b:
        st.markdown("""
        **Ringkasan Anggaran & Lokasi Proyek:**[span_10](start_span)[span_10](end_span)
        * **Total Rencana Anggaran Biaya (RAB):** **Rp 220.000.000,-** *(maksimal Rp 250 juta)*[span_11](start_span)[span_11](end_span).
        * **Alokasi Investasi Pokok:** 1 Unit Rumah pengering galvanis (Rp 15 juta), tungku biomassa cor beton (Rp 15 juta), pipa stainless steel, blower induksi, filter ganda (HEPA & Coarse), dan modul sensor IoT[span_12](start_span)[span_12](end_span).
        * **Mitra Sasaran & Lokasi:** Sentra Pertanian Terpadu Pusat Organik PUSAKA BLORA, Desa Sidorejo, Kec. Kedungtuban, Kab. Blora[span_13](start_span)[span_13](end_span).
        * **Mitra Kolaborasi:** PT Pertamina EP Cepu Field Cepu[span_14](start_span)[span_14](end_span).
        """)

# ==============================================================================
# 6. FOOTER RESMI TIM PENGUSUL
# ==============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #697184; font-size: 12px; line-height: 1.6;">
    <strong>SI-PADI: Pengering Padi Surya Terintegrasi IoT</strong>[span_15](start_span)[span_15](end_span)<br>
    Kompetisi Inovasi Teknologi dan Energi — Program PFsains Pertamina Foundation 2026[span_16](start_span)[span_16](end_span)<br>
    <strong>Tim Pengusul:</strong> Prof. Dr. Ir. Widayat, S.T., M.T., IPM., ASEAN Eng. (Ketua · Undip) · Ir. Ali Mutakin, S.Kom. · Yusron Mahendra Diwiyanto, S.T.[span_17](start_span)[span_17](end_span)<br>
    Pusat Organik PUSAKA BLORA · PT Pertamina EP Cepu Field Cepu[span_18](start_span)[span_18](end_span)
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 7. ENGINE AUTO-PLAY LOOP (BERJALAN TIAP 3 DETIK SELAMA PRESENTASI)
# ==============================================================================
if st.session_state.auto_play and st.session_state.detik_berjalan < detik_maks:
    time.sleep(3)
    st.session_state.detik_berjalan = min(detik_maks, st.session_state.detik_berjalan + 5)
    update_kondisi_zona(5)
    st.rerun()

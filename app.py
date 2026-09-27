import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA INDUSTRIAL DARK (SCADA STANDARD)
# ==============================================================================
st.set_page_config(
    page_title="SI-PADI — Telemetri & Pusat Kendali IoT",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeksi CSS Standar Industrial UI / Human-Machine Interface
st.markdown("""
<style>
    /* Dasar Aplikasi */
    .stApp {
        background-color: #0f1015;
        color: #e2e4e9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }
    
    /* Panel Navigasi Atas */
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
        font-family: "JetBrains Mono", "SF Mono", Consolas, monospace;
        font-weight: 600;
        letter-spacing: 0.8px;
    }

    /* Kartu Ringkasan Eksekutif (Top KPI Cards) */
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
        font-feature-settings: "tnum";
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

    /* Kartu Unit Bak Datar */
    .chamber-card {
        background-color: #141720;
        border: 1px solid #232838;
        border-radius: 8px;
        padding: 16px;
        height: 100%;
        transition: border 0.2s ease-in-out;
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
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-pill-done {
        background-color: #12281a;
        color: #3fb950;
        border: 1px solid #238636;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
        font-feature-settings: "tnum";
    }

    /* Container Panel Kontrol */
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
        letter-spacing: 0.5px;
        color: #d19a38;
        border-bottom: 1px solid #202534;
        padding-bottom: 8px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. INISIALISASI SESI & DATA TELEMETRI
# ==============================================================================
if 'initialized' not in st.session_state:
    st.session_state.menit_berjalan = 12
    st.session_state.cuaca = "☀️ Surya Penuh (Suplai PLTS Penuh)"
    st.session_state.mode_operasi = "Otomatis (Closed-Loop PID)"
    st.session_state.bak_data = {
        "Bak 1": {
            "suhu": 40.7,
            "target_suhu": 42,
            "ka": 25.7,
            "target_ka": 14.0,
            "blower": True,
            "pemanas": True,
            "status": "Proses",
            "history": [
                {"Menit": 0, "Suhu": 30.0, "Kadar Air": 27.7},
                {"Menit": 4, "Suhu": 35.2, "Kadar Air": 27.1},
                {"Menit": 8, "Suhu": 39.0, "Kadar Air": 26.4},
                {"Menit": 12, "Suhu": 40.7, "Kadar Air": 25.7}
            ]
        },
        "Bak 2": {
            "suhu": 45.1,
            "target_suhu": 45,
            "ka": 17.9,
            "target_ka": 14.0,
            "blower": True,
            "pemanas": True,
            "status": "Proses",
            "history": [
                {"Menit": 0, "Suhu": 30.0, "Kadar Air": 27.7},
                {"Menit": 4, "Suhu": 38.0, "Kadar Air": 23.5},
                {"Menit": 8, "Suhu": 43.1, "Kadar Air": 20.2},
                {"Menit": 12, "Suhu": 45.1, "Kadar Air": 17.9}
            ]
        },
        "Bak 3": {
            "suhu": 41.3,
            "target_suhu": 40,
            "ka": 26.4,
            "target_ka": 14.0,
            "blower": True,
            "pemanas": True,
            "status": "Proses",
            "history": [
                {"Menit": 0, "Suhu": 30.0, "Kadar Air": 27.7},
                {"Menit": 4, "Suhu": 34.5, "Kadar Air": 27.4},
                {"Menit": 8, "Suhu": 38.2, "Kadar Air": 26.9},
                {"Menit": 12, "Suhu": 41.3, "Kadar Air": 26.4}
            ]
        }
    }
    st.session_state.initialized = True

# ==============================================================================
# 3. SIDEBAR SIMULASI DINAMIKA SISTEM
# ==============================================================================
st.sidebar.markdown("### 🎛️ Konsol Eksekusi Siklus")
st.sidebar.caption("Simulasi Kinetika Pengeringan Gabah (Pre-Commissioning)")

col_btn_a, col_btn_b = st.sidebar.columns(2)
with col_btn_a:
    btn_maju_30 = st.sidebar.button("⏩ +30 Menit", use_container_width=True)
with col_btn_b:
    btn_maju_60 = st.sidebar.button("⏩ +1 Jam", use_container_width=True)

if st.sidebar.button("🔄 Reset Siklus Operasi", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⛅ Sumber Pasokan Energi Primer")
pilihan_cuaca = st.sidebar.selectbox(
    "Status Radiasi & Grid Listrik:",
    [
        "☀️ Surya Penuh (Suplai PLTS Penuh)", 
        "☁️ Berawan (Hibrida PLTS & Biomassa)", 
        "🌧️ Hujan / Malam Hari (Biomassa Penuh)"
    ]
)
st.session_state.cuaca = pilihan_cuaca

# Logika Kinetika Pengeringan Gabah (Model Laju Penurunan Kadar Air)
def perbarui_kinetika(durasi_menit):
    st.session_state.menit_berjalan += durasi_menit
    for _, bak in st.session_state.bak_data.items():
        if bak["status"] == "Selesai":
            continue
        
        # Dinamika Suhu Operasional
        if bak["pemanas"]:
            if bak["suhu"] < bak["target_suhu"]:
                bak["suhu"] = min(float(bak["target_suhu"]), bak["suhu"] + 0.9 * (durasi_menit / 15))
            else:
                bak["suhu"] = max(float(bak["target_suhu"]), bak["suhu"] - 0.3 * (durasi_menit / 15))
        else:
            bak["suhu"] = max(30.0, bak["suhu"] - 2.5 * (durasi_menit / 15))

        # Penurunan Kadar Air Gabah Berdasarkan Aliran Udara & Kalor
        if bak["blower"] and bak["pemanas"]:
            laju_reduksi = 0.55 * (durasi_menit / 30)
            bak["ka"] = max(float(bak["target_ka"]), round(bak["ka"] - laju_reduksi, 1))
        elif bak["blower"] and not bak["pemanas"]:
            laju_reduksi = 0.12 * (durasi_menit / 30)
            bak["ka"] = max(float(bak["target_ka"]), round(bak["ka"] - laju_reduksi, 1))

        if bak["ka"] <= bak["target_ka"]:
            bak["status"] = "Selesai"

        bak["history"].append({
            "Menit": st.session_state.menit_berjalan,
            "Suhu": round(bak["suhu"], 1),
            "Kadar Air": round(bak["ka"], 1)
        })

if btn_maju_30:
    perbarui_kinetika(30)
    st.rerun()

if btn_maju_60:
    perbarui_kinetika(60)
    st.rerun()

# ==============================================================================
# 4. HEADER UTAMA (SCADA NAVBAR)
# ==============================================================================
waktu_server = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div class="top-navbar">
    <div>
        <div class="navbar-title">🌾 SI-PADI — Panel Monitoring Pengering Gabah Padi</div>
        <div class="navbar-sub">Konfigurasi Pengering 3 Bak Datar Aktif · Telemetri Terintegrasi IoT · PUSAKA BLORA</div>
    </div>
    <div style="display:flex; align-items:center; gap:14px;">
        <span style="font-size:12px; color:#3fb950; font-weight:600;">● SISTEM AKTIF</span>
        <div class="clock-badge">{waktu_server} WIB</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Kalkulasi Metrik Global
list_ka = [b["ka"] for b in st.session_state.bak_data.values()]
rata_ka = round(sum(list_ka) / len(list_ka), 1)
total_selesai = sum(1 for b in st.session_state.bak_data.values() if b["status"] == "Selesai")

delta_ka = max(0.0, max(list_ka) - 14.0)
estimasi_total_menit = int((delta_ka / 0.55) * 30)
est_jam = estimasi_total_menit // 60
est_mnt = estimasi_total_menit % 60

# ==============================================================================
# 5. TAB NAVIGASI SISTEM
# ==============================================================================
tab_dashboard, tab_hmi, tab_spek = st.tabs([
    "📊 Panel Operasional 3 Bak Datar", 
    "🔄 Diagram Alir Sistem (3D Isometrik HMI)", 
    "📑 Spesifikasi Desain & Rencana Anggaran (RAB)"
])

# ------------------------------------------------------------------------------
# TAB 1: DASHBOARD OPERASIONAL
# ------------------------------------------------------------------------------
with tab_dashboard:
    # 3 Kartu Indikator Utama
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Rata-Rata Kadar Air Seluruh Bak</div>
            <div class="summary-metric">{rata_ka:.1f} <span class="summary-unit">%</span></div>
            <div class="summary-subtext">Standar Target Akhir SNI 6128:2020: 14.0%</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Status Batch Operasional</div>
            <div class="summary-metric">{total_selesai} <span class="summary-unit">/ 3 Selesai</span></div>
            <div class="summary-subtext">{"Semua unit bak dalam siklus aktif" if total_selesai < 3 else "Seluruh muatan gabah telah memenuhi ambang simpan"}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Estimasi Sisa Durasi Proses</div>
            <div class="summary-metric">{est_jam} <span class="summary-unit">jam</span> {est_mnt} <span class="summary-unit">mnt</span></div>
            <div class="summary-subtext">Kalkulasi dinamis gradien penurunan kadar air</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # Tata Letak Workspace: 3 Kolom Bak di Kiri, Panel Kontrol Parameter di Kanan
    col_workspace_l, col_workspace_r = st.columns([2.2, 1.0])

    with col_workspace_l:
        st.markdown("##### Status Telemetri Real-Time Tiap Unit Pengering")
        bak_fokus = st.radio(
            "Pilih Unit untuk Fokus Analitik & Pengaturan Aktuator:",
            ["Bak 1", "Bak 2", "Bak 3"],
            horizontal=True
        )

        col_b1, col_b2, col_b3 = st.columns(3)
        slot_kolom = {"Bak 1": col_b1, "Bak 2": col_b2, "Bak 3": col_b3}

        for nama_bak, slot in slot_kolom.items():
            dt_bak = st.session_state.bak_data[nama_bak]
            badge_tipe = "status-pill-done" if dt_bak["status"] == "Selesai" else "status-pill-active"
            border_fokus = "border: 1.5px solid #d19a38; box-shadow: 0 0 10px rgba(209,154,56,0.25);" if nama_bak == bak_fokus else ""

            with slot:
                st.markdown(f"""
                <div class="chamber-card" style="{border_fokus}">
                    <div class="chamber-header">
                        <span class="chamber-name">{nama_bak}</span>
                        <span class="{badge_tipe}">{dt_bak["status"]}</span>
                    </div>
                    <div class="param-row">
                        <span>Suhu Udara Masuk:</span>
                        <span class="param-val">{dt_bak['suhu']:.1f} °C</span>
                    </div>
                    <div class="param-row">
                        <span>Target Setpoint:</span>
                        <span>{dt_bak['target_suhu']} °C</span>
                    </div>
                    <div class="param-row" style="margin-top:4px;">
                        <span>Kadar Air Aktual:</span>
                        <span class="param-val" style="color:#d19a38;">{dt_bak['ka']:.1f} %</span>
                    </div>
                    <div class="param-row">
                        <span>Batas Aman SNI:</span>
                        <span>{dt_bak['target_ka']:.1f} %</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:14px; padding-top:8px; border-top:1px solid #1f2431; font-size:11px;">
                        <span style="color:{'#3fb950' if dt_bak['blower'] else '#697184'}; font-weight:600;">
                            🌀 BLOWER: {'ON' if dt_bak['blower'] else 'OFF'}
                        </span>
                        <span style="color:{'#e5a43b' if dt_bak['pemanas'] else '#697184'}; font-weight:600;">
                            🔥 PEMANAS: {'ON' if dt_bak['pemanas'] else 'OFF'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

        # Kartu Grafik Riwayat Proses
        bak_aktif = st.session_state.bak_data[bak_fokus]
        st.markdown(f"""
        <div class="summary-card" style="margin-bottom: 10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:15px; font-weight:700; color:#f1f3f7;">Grafik Dinamika Kinetika — {bak_fokus}</span>
                    <div style="font-size:12px; color:#8890a1; margin-top:2px;">Korelasi Suhu Termal (°C) terhadap Dehidrasi Kadar Air (%)</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:11px; color:#8890a1;">Durasi Operasi Berjalan</div>
                    <div style="font-size:18px; font-weight:700; color:#f1f3f7;">{st.session_state.menit_berjalan} <span style="font-size:12px; font-weight:normal; color:#8890a1;">Menit</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_telemetri = pd.DataFrame(bak_aktif["history"]).set_index("Menit")
        st.line_chart(df_telemetri[["Suhu", "Kadar Air"]], color=["#d19a38", "#3fb950"])

    with col_workspace_r:
        # Panel Konfigurasi Aktuator & Setpoint
        st.markdown(f"""
        <div class="control-panel-box">
            <div class="control-panel-heading">Pengaturan Parameter — {bak_fokus}</div>
        """, unsafe_allow_html=True)

        sp_ka = st.slider(
            "Batas Akhir Kadar Air (SNI %):", 
            min_value=11.0, 
            max_value=16.0, 
            value=float(bak_aktif["target_ka"]), 
            step=0.5,
            help="Ambang batas dehidrasi gabah sebelum siklus dinyatakan selesai."
        )
        sp_suhu = st.slider(
            "Suhu Udara Pengering Target (°C):", 
            min_value=35, 
            max_value=60, 
            value=int(bak_aktif["target_suhu"]), 
            step=1,
            help="Suhu udara bersih optimal agar nutrisi benih padi organik tidak rusak."
        )
        bak_aktif["target_ka"] = sp_ka
        bak_aktif["target_suhu"] = sp_suhu

        st.markdown("<div style='font-size:12px; font-weight:600; color:#8890a1; margin-top:14px; margin-bottom:8px;'>Kendali Aktuator Mandiri:</div>", unsafe_allow_html=True)
        col_sw1, col_sw2 = st.columns(2)
        with col_sw1:
            bak_aktif["blower"] = st.toggle("Blower Udara", value=bak_aktif["blower"])
        with col_sw2:
            bak_aktif["pemanas"] = st.toggle("Elemen Pemanas", value=bak_aktif["pemanas"])

        mode_terpilih = st.selectbox("Algoritma Pengendalian:", ["Otomatis (Closed-Loop PID)", "Manual Override System"])
        st.session_state.mode_operasi = mode_terpilih

        st.markdown(f"""
            <div style="font-size:12px; color:#8890a1; margin-top:14px; padding-top:10px; border-top:1px solid #202534;">
                Status Kontrol: <strong style="color:#d19a38;">{mode_terpilih.split()[0]}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tombol Unduh Telemetri
        st.download_button(
            label="📥 Ekspor Data Log Siklus (.CSV)",
            data=df_telemetri.to_csv().encode('utf-8'),
            file_name=f"log_kinetika_{bak_fokus.replace(' ', '_').lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ------------------------------------------------------------------------------
# TAB 2: HMI DIGITAL TWIN (REPRESENTASI PRESISI GAMBAR 1 REVISI)
# ------------------------------------------------------------------------------
with tab_hmi:
    st.markdown("### 🗺️ Skema Integrasi Termal & Pembangkit EBT SI-PADI")
    st.caption("Visualisasi Terpadu Stasiun Bioenergi, Menara Penukar Panas (HE), Ruang Rak Pengering, dan Array PLTS 4.000 Wp")

    # Parameter Dinamis untuk Sinkronisasi SVG
    if "Surya" in st.session_state.cuaca:
        suplai_plts_wp = 3920
        status_baterai = 96.5
        suhu_ruang_bakar = 370
        aliran_energi = "PLTS Mandiri (Beban Penuh Tercover Surya)"
    elif "Berawan" in st.session_state.cuaca:
        suplai_plts_wp = 1850
        status_baterai = 78.0
        suhu_ruang_bakar = 415
        aliran_energi = "Hibrida Seimbang (PLTS 50% · Biomassa 50%)"
    else:
        suplai_plts_wp = 0
        status_baterai = 54.0
        suhu_ruang_bakar = 460
        aliran_energi = "Biomassa Termal Penuh (Dukungan Baterai Storage)"

    ka_b1 = st.session_state.bak_data["Bak 1"]["ka"]
    ka_b2 = st.session_state.bak_data["Bak 2"]["ka"]
    ka_b3 = st.session_state.bak_data["Bak 3"]["ka"]

    svg_hmi_industrial = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 520" width="100%" height="100%" style="background-color: #12141c; border-radius: 10px; border: 1px solid #232838; font-family: -apple-system, sans-serif;">
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
      <rect x="20" y="20" width="600" height="480" rx="8" fill="#161822" stroke="#2b3246" stroke-width="1.5"/>
      <rect x="35" y="32" width="310" height="26" rx="4" fill="#202534"/>
      <text x="45" y="50" fill="#e2e4e9" font-size="12" font-weight="700" letter-spacing="0.5">1. STASIUN BIOENERGI &amp; GAS CLEANING</text>

      <!-- Tungku Biomassa Cor Beton -->
      <rect x="40" y="180" width="160" height="180" rx="6" fill="#1d202d" stroke="#d19a38" stroke-width="2"/>
      <text x="120" y="215" fill="#d19a38" font-size="12" font-weight="700" text-anchor="middle">TUNGKU BIOMASSA</text>
      <text x="120" y="235" fill="#8890a1" font-size="10" text-anchor="middle">Limbah Batang Padi</text>
      <rect x="60" y="255" width="120" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="120" y="285" fill="#ff7b72" font-size="18" font-weight="700" text-anchor="middle">{suhu_ruang_bakar} °C</text>
      <text x="120" y="340" fill="#8890a1" font-size="9" text-anchor="middle">Sensor Suhu Ruang Bakar</text>

      <!-- Cerobong Peningkat & Filtrasi Partikulat Ganda -->
      <path d="M 200 240 L 230 240" stroke="#d19a38" stroke-width="3" fill="none" marker-end="url(#arrow-amber)"/>
      <rect x="230" y="100" width="95" height="170" rx="6" fill="#1a1d29" stroke="#8890a1" stroke-width="1.5"/>
      <text x="277" y="125" fill="#e2e4e9" font-size="10" font-weight="700" text-anchor="middle">HEAT RISER</text>
      <text x="277" y="140" fill="#8890a1" font-size="9" text-anchor="middle">(Cerobong)</text>
      <line x1="230" y1="160" x2="325" y2="160" stroke="#333a4d" stroke-width="2"/>
      <text x="277" y="185" fill="#d19a38" font-size="9" font-weight="600" text-anchor="middle">Filter Kasar</text>
      <line x1="230" y1="205" x2="325" y2="205" stroke="#333a4d" stroke-width="2"/>
      <text x="277" y="230" fill="#3fb950" font-size="9" font-weight="600" text-anchor="middle">HEPA &amp; VOC Gas</text>

      <!-- Pelepasan Gas Bersih -->
      <path d="M 277 100 L 277 75 L 360 75" stroke="#3fb950" stroke-width="3" fill="none" marker-end="url(#arrow-green)"/>
      <text x="365" y="70" fill="#3fb950" font-size="9" font-weight="600">Aliran Emisi Bersih Terfiltrasi</text>

      <!-- Menara Koil Penukar Panas (Heat Exchanger Tower) -->
      <rect x="345" y="120" width="110" height="240" rx="6" fill="#182026" stroke="#3fb950" stroke-width="2"/>
      <text x="400" y="148" fill="#3fb950" font-size="11" font-weight="700" text-anchor="middle">HEAT EXCHANGER</text>
      <text x="400" y="165" fill="#8890a1" font-size="9" text-anchor="middle">Penukar Kalor Hibrida</text>
      <circle cx="400" cy="210" r="26" fill="#0f1015" stroke="#3fb950" stroke-width="2"/>
      <text x="400" y="215" fill="#3fb950" font-size="12" font-weight="700" text-anchor="middle">85%</text>
      <text x="400" y="270" fill="#58a6ff" font-size="9" text-anchor="middle">Inlet Udara Bersih</text>
      <text x="400" y="285" fill="#e2e4e9" font-size="9" text-anchor="middle">Dipanaskan Bersih</text>
      <text x="400" y="340" fill="#8890a1" font-size="9" text-anchor="middle">Efisiensi Termal Optimal</text>

      <!-- Saluran Distribusi Udara Panas ke Rumah Pengering -->
      <path d="M 455 240 L 485 240" stroke="#d19a38" stroke-width="4" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- Rumah Pengering Gabah 3 Bak Datar -->
      <rect x="485" y="90" width="120" height="300" rx="6" fill="#1a1c24" stroke="#d19a38" stroke-width="2"/>
      <text x="545" y="120" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">RUMAH PENGERING</text>
      <text x="545" y="136" fill="#8890a1" font-size="9" text-anchor="middle">Sistem 3 Bak Datar</text>
      
      <!-- Representasi 3 Bak Pengering -->
      <rect x="495" y="160" width="100" height="42" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="545" y="178" fill="#e2e4e9" font-size="10" font-weight="600" text-anchor="middle">Bak 1</text>
      <text x="545" y="193" fill="#d19a38" font-size="10" font-weight="700" text-anchor="middle">KA: {ka_b1:.1f}%</text>

      <rect x="495" y="215" width="100" height="42" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="545" y="233" fill="#e2e4e9" font-size="10" font-weight="600" text-anchor="middle">Bak 2</text>
      <text x="545" y="248" fill="#d19a38" font-size="10" font-weight="700" text-anchor="middle">KA: {ka_b2:.1f}%</text>

      <rect x="495" y="270" width="100" height="42" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="545" y="288" fill="#e2e4e9" font-size="10" font-weight="600" text-anchor="middle">Bak 3</text>
      <text x="545" y="303" fill="#d19a38" font-size="10" font-weight="700" text-anchor="middle">KA: {ka_b3:.1f}%</text>

      <text x="545" y="350" fill="#3fb950" font-size="9" font-weight="600" text-anchor="middle">Blower Udara Aktif</text>
      <text x="545" y="365" fill="#8890a1" font-size="9" text-anchor="middle">Kapasitas: 1 Ton / Siklus</text>

      <!-- 2. SISTEM PEMBANGKIT SURYA (PLTS DARAT 4.000 Wp) -->
      <rect x="640" y="20" width="340" height="480" rx="8" fill="#161822" stroke="#2b3246" stroke-width="1.5"/>
      <rect x="655" y="32" width="260" height="26" rx="4" fill="#202534"/>
      <text x="665" y="50" fill="#e2e4e9" font-size="12" font-weight="700" letter-spacing="0.5">2. SISTEM ENERGI SURYA (PLTS DARAT)</text>

      <!-- PV Array -->
      <rect x="665" y="80" width="290" height="110" rx="6" fill="#151d2a" stroke="#388bfd" stroke-width="2"/>
      <text x="810" y="120" fill="#58a6ff" font-size="13" font-weight="700" text-anchor="middle">ARRAY PANEL SURYA</text>
      <text x="810" y="145" fill="#e2e4e9" font-size="18" font-weight="700" text-anchor="middle">{suplai_plts_wp} Wp</text>
      <text x="810" y="165" fill="#8890a1" font-size="10" text-anchor="middle">Kapasitas Terpasang: 4.000 Wp Off-Grid</text>

      <path d="M 810 190 L 810 220" stroke="#58a6ff" stroke-width="3" fill="none" marker-end="url(#arrow-blue)"/>

      <!-- MPPT Charge Controller -->
      <rect x="710" y="220" width="200" height="60" rx="6" fill="#1d202d" stroke="#d19a38" stroke-width="1.5"/>
      <text x="810" y="244" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">SOLAR CHARGE CONTROLLER</text>
      <text x="810" y="264" fill="#3fb950" font-size="10" font-weight="600" text-anchor="middle">Efisiensi Pelacakan MPPT: 98%</text>

      <path d="M 810 280 L 810 310" stroke="#3fb950" stroke-width="3" fill="none" marker-end="url(#arrow-green)"/>

      <!-- Baterai Storage -->
      <rect x="710" y="310" width="200" height="60" rx="6" fill="#1d202d" stroke="#3fb950" stroke-width="1.5"/>
      <text x="810" y="334" fill="#3fb950" font-size="11" font-weight="700" text-anchor="middle">BATERAI PENYIMPANAN</text>
      <text x="810" y="355" fill="#e2e4e9" font-size="13" font-weight="700" text-anchor="middle">{status_baterai:.1f}% Kapasitas Tersedia</text>

      <!-- Beban Kelistrikan Terpasang -->
      <rect x="665" y="390" width="290" height="85" rx="6" fill="#0f1015" stroke="#2b3246"/>
      <text x="680" y="415" fill="#8890a1" font-size="10" font-weight="600">PENYALURAN DAYA OPERASIONAL:</text>
      <text x="680" y="435" fill="#e2e4e9" font-size="10">• Blower Sirkulasi Udara Termal (2x 500W)</text>
      <text x="680" y="452" fill="#e2e4e9" font-size="10">• Mikrokontroler IoT, Sensor &amp; Gateway Data</text>
    </svg>
    """
    st.components.v1.html(svg_hmi_industrial, height=540)

# ------------------------------------------------------------------------------
# TAB 3: SPESIFIKASI DESAIN & RENCANA ANGGARAN BIAYA (RAB)
# ------------------------------------------------------------------------------
with tab_spek:
    st.markdown("### 📋 Spesifikasi Keteknikan & Rencana Anggaran Biaya Revisi")
    st.caption("Diselaraskan Penuh dengan Draf Final Usulan PFsains Pertamina Foundation 2026[cite: 7]")

    col_spec_a, col_spec_b = st.columns(2)
    with col_spec_a:
        st.markdown("""
        **Parameter Teknis Unit SI-PADI[cite: 7]:**
        * **Konfigurasi Unit:** Rumah Pengering Hibrida 3 Bak Datar Aktif (*Flat-Bed Dryers*)[cite: 7].
        * **Dimensi Fasilitas:** $\\pm 6\\text{ m} \\times 4\\text{ m} \\times 3\\text{ m}$ berangka baja galvanis dengan insulasi polikarbonat penahan radiasi UV[cite: 7].
        * **Kapasitas Olah:** $\\pm 1\\text{ Ton}$ gabah segar per siklus pengeringan (durasi 18–24 jam)[cite: 7].
        * **Profil Kadar Air Gabah:** Diturunkan dari $27,72\\%$ (basis basah) menjadi $\\leq 14,0\\%$ (memenuhi standar mutu simpan SNI 6128:2020)[cite: 7].
        * **Sumber Daya Termal & Elektrik:** Pembangkit Listrik Tenaga Surya (PLTS) $4.000\\text{ Wp}$ dilengkapi baterai penyimpanan serta tungku biomassa pembakar limbah batang padi[cite: 7].
        * **Kematangan Inovasi:** Tingkat Kesiapan Teknologi (TKT) level 6–7 (prototipe skala penuh teruji di lingkungan operasional nyata)[cite: 7].
        """)

    with col_spec_b:
        st.markdown("""
        **Ringkasan Anggaran & Lokasi Proyek[cite: 7]:**
        * **Total Rencana Anggaran Biaya (RAB):** **Rp 220.000.000,-** *(sesuai ketentuan plafon maksimal Rp 250 juta)*[cite: 7].
        * **Alokasi Investasi Pokok:** Konstruksi rumah pengering galvanis, tungku biomassa cor beton tahan api, pipa stainless steel, blower induksi, filter partikulat ganda (HEPA & Coarse), dan instrumentasi sensor telemetri[cite: 7].
        * **Mitra Sasaran & Lokasi:** Sentra Pertanian Terpadu Pusat Organik PUSAKA BLORA, Desa Sidorejo, Kecamatan Kedungtuban, Kabupaten Blora, Jawa Tengah[cite: 7].
        * **Mitra Kolaborasi Industri:** PT Pertamina EP Cepu Field Cepu[cite: 7].
        """)

# ==============================================================================
# 6. FOOTER RESMI TIM PENGUSUL
# ==============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #697184; font-size: 12px; line-height: 1.6;">
    <strong>SI-PADI: Pengering Padi Surya Terintegrasi IoT</strong>[cite: 7]<br>
    Kompetisi Inovasi Teknologi dan Energi — Program PFsains Pertamina Foundation 2026[cite: 7]<br>
    <strong>Tim Pengusul:</strong> Prof. Dr. Ir. Widayat, S.T., M.T., IPM., ASEAN Eng. (Ketua · Undip) · Ir. Ali Mutakin, S.Kom. · Yusron Mahendra Diwiyanto, S.T.[cite: 7]<br>
    Pusat Organik PUSAKA BLORA · PT Pertamina EP Cepu Field Cepu[cite: 7]
</div>
""", unsafe_allow_html=True)

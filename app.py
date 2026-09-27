import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN DARK THEME PERSIS GAMBAR 4 ---
st.set_page_config(
    page_title="Panel Monitoring — Pengering Gabah Padi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Dark Industrial Palette (#12110c / #1b1913 / Aksen Amber)
st.markdown("""
<style>
    .stApp {
        background-color: #12110c;
        color: #d6d3cd;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding-bottom: 12px;
        border-bottom: 1px solid #2a261c;
        margin-bottom: 20px;
    }
    .main-title {
        font-size: 24px;
        font-weight: 700;
        color: #f5f3ef;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .sub-title {
        font-size: 13px;
        color: #8c8577;
        margin-top: 4px;
    }
    .digital-clock {
        background-color: #1e1b14;
        border: 1px solid #332d20;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 15px;
        color: #c99738;
        font-family: monospace;
        font-weight: 600;
    }
    .summary-card {
        background-color: #1a1812;
        border: 1px solid #2e291f;
        border-radius: 8px;
        padding: 16px 20px;
        height: 100%;
    }
    .summary-label {
        font-size: 12px;
        color: #8c8577;
        margin-bottom: 6px;
    }
    .summary-val-large {
        font-size: 34px;
        font-weight: 700;
        color: #d99b26;
        line-height: 1.1;
    }
    .summary-val-unit {
        font-size: 18px;
        font-weight: normal;
        color: #8c8577;
    }
    .summary-footer {
        font-size: 12px;
        color: #716b5f;
        margin-top: 6px;
    }
    .bak-card {
        background-color: #1a1812;
        border: 1px solid #2e291f;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 15px;
    }
    .bak-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .bak-title {
        font-size: 16px;
        font-weight: 700;
        color: #f5f3ef;
    }
    .badge-proses {
        background-color: #2b2414;
        color: #d99b26;
        border: 1px solid #57431e;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-selesai {
        background-color: #132b17;
        color: #3fb950;
        border: 1px solid #238636;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 600;
    }
    .sensor-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #8c8577;
        margin-bottom: 8px;
    }
    .sensor-highlight {
        font-size: 16px;
        font-weight: 700;
        color: #f5f3ef;
    }
    .control-box {
        background-color: #1a1812;
        border: 1px solid #2e291f;
        border-radius: 8px;
        padding: 18px;
    }
    .control-title {
        font-size: 15px;
        font-weight: 700;
        color: #f5f3ef;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INISIALISASI SESSION STATE ---
if 'initialized' not in st.session_state:
    st.session_state.menit_berjalan = 12
    st.session_state.cuaca = "☀️ Cerah (PLTS 100%)"
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
                {"Menit": 0, "Suhu": 30.0, "KA": 27.7},
                {"Menit": 4, "Suhu": 35.2, "KA": 27.1},
                {"Menit": 8, "Suhu": 39.0, "KA": 26.4},
                {"Menit": 12, "Suhu": 40.7, "KA": 25.7}
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
                {"Menit": 0, "Suhu": 30.0, "KA": 27.7},
                {"Menit": 4, "Suhu": 38.0, "KA": 23.5},
                {"Menit": 8, "Suhu": 43.1, "KA": 20.2},
                {"Menit": 12, "Suhu": 45.1, "KA": 17.9}
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
                {"Menit": 0, "Suhu": 30.0, "KA": 27.7},
                {"Menit": 4, "Suhu": 34.5, "KA": 27.4},
                {"Menit": 8, "Suhu": 38.2, "KA": 26.9},
                {"Menit": 12, "Suhu": 41.3, "KA": 26.4}
            ]
        }
    }
    st.session_state.initialized = True

# --- 3. SIDEBAR SIMULASI PROSES ---
st.sidebar.markdown("### ⏱️ Kontrol Simulasi Waktu")
st.sidebar.caption("Jalankan siklus pengeringan untuk melihat reaksi IoT")

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    btn_step_30 = st.sidebar.button("⏩ +30 Menit")
with col_s2:
    btn_step_60 = st.sidebar.button("⏩ +1 Jam")

if st.sidebar.button("🔄 Reset ke Awal"):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ☀️ Kondisi Sumber Energi")
cuaca_opsi = st.sidebar.radio(
    "Pasokan PLTS:",
    ["☀️ Cerah (PLTS 100%)", "☁️ Mendung (Hibrida 50%)", "🌧️ Hujan / Malam (Biomassa 100%)"]
)
st.session_state.cuaca = cuaca_opsi

# Logika Maju Waktu Pengeringan
def maju_waktu(menit_tambah):
    st.session_state.menit_berjalan += menit_tambah
    for b_nama, b in st.session_state.bak_data.items():
        if b["status"] == "Selesai":
            continue
        
        # Dinamika Suhu
        if b["pemanas"]:
            if b["suhu"] < b["target_suhu"]:
                b["suhu"] = min(float(b["target_suhu"]), b["suhu"] + 0.8 * (menit_tambah / 15))
            else:
                b["suhu"] = max(float(b["target_suhu"]), b["suhu"] - 0.4 * (menit_tambah / 15))
        else:
            b["suhu"] = max(31.0, b["suhu"] - 2.0 * (menit_tambah / 15))

        # Dinamika Penurunan Kadar Air
        if b["blower"] and b["pemanas"]:
            laju_ka = 0.55 * (menit_tambah / 30)
            b["ka"] = max(float(b["target_ka"]), round(b["ka"] - laju_ka, 1))
        elif b["blower"] and not b["pemanas"]:
            laju_ka = 0.15 * (menit_tambah / 30)
            b["ka"] = max(float(b["target_ka"]), round(b["ka"] - laju_ka, 1))

        if b["ka"] <= b["target_ka"]:
            b["status"] = "Selesai"

        b["history"].append({
            "Menit": st.session_state.menit_berjalan,
            "Suhu": round(b["suhu"], 1),
            "KA": round(b["ka"], 1)
        })

if btn_step_30:
    maju_waktu(30)
    st.rerun()

if btn_step_60:
    maju_waktu(60)
    st.rerun()

# --- 4. HEADER UTAMA ATAS ---
waktu_sekarang = datetime.now().strftime("%H.%M.%S")
st.markdown(f"""
<div class="top-header">
    <div>
        <div class="main-title">🌾 Panel Monitoring — Pengering Gabah Padi</div>
        <div class="sub-title">Unit pengering bak datar · 3 bak aktif · data disimulasikan untuk demo</div>
    </div>
    <div class="digital-clock">{waktu_sekarang}</div>
</div>
""", unsafe_allow_html=True)

# Perhitungan Rangkuman Metrik
semua_ka = [b["ka"] for b in st.session_state.bak_data.values()]
rata_ka = round(sum(semua_ka) / len(semua_ka), 1)
selesai_count = sum(1 for b in st.session_state.bak_data.values() if b["status"] == "Selesai")

# Estimasi Waktu Sisa
sisa_ka_terbesar = max(0.0, max(semua_ka) - 14.0)
estimasi_menit = int(sisa_ka_terbesar / 0.55 * 30)
est_jam = estimasi_menit // 60
est_mnt = estimasi_menit % 60

# TAB NAVIGASI UTAMA
tab_utama, tab_hmi, tab_spek = st.tabs([
    "📊 Panel Monitoring 3 Bak Datar", 
    "🔄 Skema Alur Alat (3D Isometrik)", 
    "📑 Data Teknis & RAB Proposal"
])

with tab_utama:
    # --- 3 KARTU METRIK ATAS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Rata-rata kadar air seluruh bak</div>
            <div class="summary-val-large">{rata_ka} <span class="summary-val-unit">%</span></div>
            <div class="summary-footer">Target akhir 14.0%</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Status bak</div>
            <div class="summary-val-large">{selesai_count} <span class="summary-val-unit">/ 3 selesai</span></div>
            <div class="summary-footer">{"Semua bak dalam kondisi normal" if selesai_count < 3 else "Seluruh proses pengeringan tuntas"}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Estimasi bak tersisa selesai</div>
            <div class="summary-val-large">{est_jam} <span class="summary-val-unit">jam</span> {est_mnt} <span class="summary-val-unit">mnt</span></div>
            <div class="summary-footer">Berdasarkan laju penurunan kadar air saat ini</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TATA LETAK 3 BAK MONITORING & PANEL KONTROL ---
    col_kiri, col_kanan = st.columns([2.1, 1])

    with col_kiri:
        # Pilihan Bak Aktif
        bak_terpilih = st.radio("Pilih Bak untuk Fokus Kontrol & Grafik:", ["Bak 1", "Bak 2", "Bak 3"], horizontal=True)
        
        # 3 Kartu Bak
        b1, b2, b3 = st.columns(3)
        kartu_cols = {"Bak 1": b1, "Bak 2": b2, "Bak 3": b3}
        
        for b_name, col_b in kartu_cols.items():
            b_info = st.session_state.bak_data[b_name]
            badge_class = "badge-selesai" if b_info["status"] == "Selesai" else "badge-proses"
            is_active_border = "border: 2px solid #d99b26;" if b_name == bak_terpilih else ""
            
            with col_b:
                st.markdown(f"""
                <div class="bak-card" style="{is_active_border}">
                    <div class="bak-header">
                        <span class="bak-title">{b_name}</span>
                        <span class="{badge_class}">{b_info["status"]}</span>
                    </div>
                    <div class="sensor-row">🌡️ Suhu <span class="sensor-highlight">{b_info['suhu']:.1f}°C</span> · target {b_info['target_suhu']}°C</div>
                    <div class="sensor-row">💧 Kadar air <span class="sensor-highlight">{b_info['ka']:.1f}%</span> · target {b_info['target_ka']}%</div>
                    <div style="display:flex; gap:6px; margin-top:12px;">
                        <span style="background:#17150f; border:1px solid #332d20; border-radius:4px; padding:3px 8px; font-size:11px; color:{'#d99b26' if b_info['blower'] else '#666'};">
                            🌀 Blower {'On' if b_info['blower'] else 'Off'}
                        </span>
                        <span style="background:#17150f; border:1px solid #332d20; border-radius:4px; padding:3px 8px; font-size:11px; color:{'#d99b26' if b_info['pemanas'] else '#666'};">
                            🔥 Pemanas {'On' if b_info['pemanas'] else 'Off'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Kartu Grafik Proses Terpilih
        curr_b = st.session_state.bak_data[bak_terpilih]
        st.markdown(f"""
        <div class="bak-card" style="margin-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-weight:700; font-size:15px; color:#f5f3ef;">Grafik proses — {bak_terpilih}</span>
                <span style="font-size:12px; color:#8c8577;">suhu (°C) &amp; kadar air (%)</span>
            </div>
            <div style="display:flex; gap:30px; margin-bottom:12px;">
                <div>
                    <div style="font-size:11px; color:#8c8577;">Suhu saat ini</div>
                    <div style="font-size:22px; font-weight:700; color:#d99b26;">{curr_b['suhu']:.1f}°C</div>
                </div>
                <div>
                    <div style="font-size:11px; color:#8c8577;">Kadar air saat ini</div>
                    <div style="font-size:22px; font-weight:700; color:#d99b26;">{curr_b['ka']:.1f}%</div>
                </div>
                <div>
                    <div style="font-size:11px; color:#8c8577;">Lama proses berjalan</div>
                    <div style="font-size:22px; font-weight:700; color:#f5f3ef;">{st.session_state.menit_berjalan} <span style="font-size:14px; font-weight:normal; color:#8c8577;">mnt</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_chart = pd.DataFrame(curr_b["history"]).set_index("Menit")
        st.line_chart(df_chart[["Suhu", "KA"]], color=["#d99b26", "#4caf50"])

    with col_kanan:
        # Panel Kontrol Interaktif Terhubung
        st.markdown(f"""
        <div class="control-box">
            <div class="control-title">Kontrol — {bak_terpilih}</div>
        </div>
        """, unsafe_allow_html=True)

        new_target_ka = st.slider("Target kadar air (%)", 10.0, 18.0, float(curr_b["target_ka"]), step=0.5, key="ka_slider")
        new_target_suhu = st.slider("Target suhu pengering (°C)", 30, 60, int(curr_b["target_suhu"]), step=1, key="suhu_slider")
        
        curr_b["target_ka"] = new_target_ka
        curr_b["target_suhu"] = new_target_suhu

        st.markdown("<div style='font-size:12px; color:#8c8577; margin-top:14px;'>Saklar Aktuator Alat:</div>", unsafe_allow_html=True)
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            curr_b["blower"] = st.toggle("🌀 Blower", value=curr_b["blower"])
        with col_act2:
            curr_b["pemanas"] = st.toggle("🔥 Pemanas", value=curr_b["pemanas"])

        mode_op = st.selectbox("Mode Operasi:", ["Otomatis (PID Loop)", "Manual Override"])
        st.markdown(f"""
        <div style="font-size:12px; color:#8c8577; margin-top:16px;">
            <span style="color:#d99b26;">●</span> Mode: <strong>{mode_op.split()[0].lower()}</strong>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: SKEMA ISOMETRIK TERSINKRONISASI ---
with tab_hmi:
    st.markdown("### 🗺️ Skema Integrasi Sistem Pengering Gabah SI-PADI")
    st.caption("Visualisasi Aliran Termal & Elektrikal Berdasarkan Parameter Operasional Saat Ini")

    # Status Dinamis untuk SVG
    if "Cerah" in st.session_state.cuaca:
        plts_wp = 3850
        bat_pct = 95
        suhu_furnace = 380
    elif "Mendung" in st.session_state.cuaca:
        plts_wp = 1900
        bat_pct = 75
        suhu_furnace = 420
    else:
        plts_wp = 0
        bat_pct = 50
        suhu_furnace = 460

    svg_isometrik = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 500" width="100%" height="100%" style="background-color: #16140e; border-radius: 8px; border: 1px solid #332d20; font-family: sans-serif;">
      <defs>
        <marker id="arr-gold" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#d99b26"/>
        </marker>
        <marker id="arr-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#3fb950"/>
        </marker>
      </defs>

      <!-- STASIUN BIOENERGI -->
      <rect x="20" y="20" width="600" height="460" rx="8" fill="#1b1812" stroke="#4a3c20" stroke-width="1.5"/>
      <rect x="35" y="32" width="280" height="26" rx="4" fill="#332a17"/>
      <text x="45" y="50" fill="#f5f3ef" font-size="12" font-weight="bold">1. STASIUN BIOENERGI DAN PEMBERSIHAN</text>

      <rect x="40" y="160" width="160" height="180" rx="6" fill="#241e15" stroke="#d99b26" stroke-width="2"/>
      <text x="120" y="195" fill="#d99b26" font-size="12" font-weight="bold" text-anchor="middle">TUNGKU BIOMASSA</text>
      <text x="120" y="215" fill="#8c8577" font-size="10" text-anchor="middle">Bahan: Batang Padi</text>
      <rect x="60" y="240" width="120" height="50" rx="4" fill="#12110c"/>
      <text x="120" y="270" fill="#ff7b72" font-size="16" font-weight="bold" text-anchor="middle">{suhu_furnace}°C</text>

      <!-- CEROBONG & HEPA -->
      <rect x="220" y="80" width="100" height="150" rx="4" fill="#241e15" stroke="#8c8577"/>
      <text x="270" y="105" fill="#f5f3ef" font-size="10" font-weight="bold" text-anchor="middle">HEAT RISER</text>
      <line x1="220" y1="135" x2="320" y2="135" stroke="#57431e" stroke-width="2"/>
      <text x="270" y="155" fill="#d99b26" font-size="9" text-anchor="middle">Coarse Filter</text>
      <text x="270" y="175" fill="#3fb950" font-size="9" text-anchor="middle">HEPA &amp; Gas Filter</text>
      
      <path d="M 270 80 L 270 60 L 370 60" stroke="#3fb950" stroke-width="3" fill="none" marker-end="url(#arr-green)"/>
      <text x="350" y="52" fill="#3fb950" font-size="9">Cleaned Exhaust Flow</text>

      <!-- HEAT EXCHANGER -->
      <rect x="340" y="100" width="110" height="240" rx="6" fill="#1e221b" stroke="#3fb950" stroke-width="2"/>
      <text x="395" y="125" fill="#3fb950" font-size="11" font-weight="bold" text-anchor="middle">HEAT EXCHANGER</text>
      <circle cx="395" cy="180" r="24" fill="#12110c" stroke="#3fb950"/>
      <text x="395" y="185" fill="#3fb950" font-size="12" font-weight="bold" text-anchor="middle">85%</text>

      <!-- RUMAH PENGERING 3 BAK -->
      <rect x="470" y="80" width="130" height="280" rx="6" fill="#241e15" stroke="#d99b26" stroke-width="2"/>
      <text x="535" y="110" fill="#d99b26" font-size="11" font-weight="bold" text-anchor="middle">RUMAH PENGERING</text>
      <text x="535" y="125" fill="#8c8577" font-size="9" text-anchor="middle">3 Bak Datar Aktif</text>
      
      <rect x="485" y="145" width="100" height="40" rx="3" fill="#12110c" stroke="#57431e"/>
      <text x="535" y="165" fill="#f5f3ef" font-size="10" text-anchor="middle">Bak 1: {st.session_state.bak_data['Bak 1']['ka']}%</text>
      <rect x="485" y="195" width="100" height="40" rx="3" fill="#12110c" stroke="#57431e"/>
      <text x="535" y="215" fill="#f5f3ef" font-size="10" text-anchor="middle">Bak 2: {st.session_state.bak_data['Bak 2']['ka']}%</text>
      <rect x="485" y="245" width="100" height="40" rx="3" fill="#12110c" stroke="#57431e"/>
      <text x="535" y="265" fill="#f5f3ef" font-size="10" text-anchor="middle">Bak 3: {st.session_state.bak_data['Bak 3']['ka']}%</text>

      <path d="M 450 220 L 470 220" stroke="#d99b26" stroke-width="4" fill="none" marker-end="url(#arr-gold)"/>

      <!-- PLTS DARAT -->
      <rect x="640" y="20" width="340" height="460" rx="8" fill="#1b1812" stroke="#4a3c20" stroke-width="1.5"/>
      <rect x="655" y="32" width="240" height="26" rx="4" fill="#332a17"/>
      <text x="665" y="50" fill="#f5f3ef" font-size="12" font-weight="bold">2. SISTEM ENERGI SURYA (PLTS)</text>

      <rect x="665" y="80" width="290" height="110" rx="6" fill="#172230" stroke="#388bfd" stroke-width="2"/>
      <text x="810" y="125" fill="#58a6ff" font-size="14" font-weight="bold" text-anchor="middle">☀️ PANEL SURYA DARAT</text>
      <text x="810" y="148" fill="#8c8577" font-size="11" text-anchor="middle">{plts_wp} Wp ({st.session_state.cuaca.split()[0]})</text>

      <rect x="710" y="220" width="200" height="60" rx="6" fill="#241e15" stroke="#d99b26"/>
      <text x="810" y="245" fill="#d99b26" font-size="11" font-weight="bold" text-anchor="middle">SOLAR CONTROLLER</text>
      <text x="810" y="265" fill="#3fb950" font-size="10" text-anchor="middle">MPPT On-Grid/Off-Grid</text>

      <rect x="710" y="310" width="200" height="60" rx="6" fill="#241e15" stroke="#3fb950"/>
      <text x="810" y="335" fill="#3fb950" font-size="11" font-weight="bold" text-anchor="middle">BATERAI CADANGAN</text>
      <text x="810" y="355" fill="#3fb950" font-size="13" font-weight="bold" text-anchor="middle">{bat_pct}% Tersimpan</text>

      <rect x="665" y="390" width="290" height="70" rx="6" fill="#12110c" stroke="#332d20"/>
      <text x="680" y="415" fill="#8c8577" font-size="10">⚡ Beban Terpasang:</text>
      <text x="680" y="433" fill="#f5f3ef" font-size="10">• 2 Unit Blower Sirkulasi Udara</text>
      <text x="680" y="449" fill="#f5f3ef" font-size="10">• Gateway IoT &amp; Sensor Telemetri</text>
    </svg>
    """
    st.components.v1.html(svg_isometrik, height=520)

# --- TAB 3: SPESIFIKASI TEKNIS & RAB PROPOSAL REVISI (RP 220 JUTA) ---
with tab_spek:
    st.markdown("### 📋 Spesifikasi Teknis & Rencana Anggaran Biaya")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("""
        **Spesifikasi Teknis Alat SI-PADI[cite: 7]:**
        - **Dimensi Rumah Pengering:** $\\pm 6\\text{ m} \\times 4\\text{ m} \\times 3\\text{ m}$[cite: 7]
        - **Konfigurasi:** 3 Bak Pengering Datar Aktif[cite: 7]
        - **Kapasitas Produksi:** $\\pm 1\\text{ Ton}$ gabah segar per siklus pengeringan (18–24 jam)[cite: 7]
        - **Kadar Air Awal $\\rightarrow$ Akhir:** $27.72\\%$ (basis basah) $\\rightarrow 14.0\\%$ (Standar Mutu SNI 6128:2020)[cite: 7]
        - **Sumber Daya:** PLTS Hybrid $\\pm 4.000\\text{ Wp}$ & Tungku Biomassa Batang Padi[cite: 7]
        - **Tingkat Kesiapan Teknologi:** TKT 6–7 (Prototipe teruji operasional lapangan)[cite: 7]
        """)
    with col_d2:
        st.markdown("""
        **Rencana Anggaran Biaya (RAB) Proposal[cite: 7]:**
        - **Total RAB Diusulkan:** **Rp 220.000.000,-** *(Maksimal Rp 250.000.000,-)*[cite: 7]
        - **Komponen Utama:** Kolektor Surya, Rumah Pengering Galvanis, Tungku Biomassa Cor Beton, Blower, Pipa Stainless Steel, Filter HEPA & Coarse[cite: 7]
        - **Lokasi Implementasi:** Pusat Organik PUSAKA BLORA, Desa Sidorejo, Kec. Kedungtuban, Kab. Blora[cite: 7]
        - **Mitra Lapangan:** PT Pertamina EP Cepu Field Cepu[cite: 7]
        """)

# --- FOOTER IDENTITAS RESMI ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #716b5f; font-size: 12px; line-height: 1.6;">
    <strong>SI-PADI — Kompetisi Inovasi Teknologi dan Energi Program PFsains 2026</strong>[cite: 7]<br>
    Ketua Tim: Prof. Dr. Ir. Widayat, S.T., M.T., IPM., ASEAN Eng. (Universitas Diponegoro)[cite: 7]<br>
    Anggota: Ir. Ali Mutakin, S.Kom. · Yusron Mahendra Diwiyanto, S.T.[cite: 7]<br>
    Pusat Organik PUSAKA BLORA · Pertamina Foundation[cite: 7]
</div>
""", unsafe_allow_html=True)

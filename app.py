import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN DARK THEME PERSIS GAMBAR 4 ---
st.set_page_config(
    page_title="Panel Monitoring — Pengering Gabah Padi",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Dark Industrial Palette (#12110c / #1b1913 / Aksen Gold-Amber)
st.markdown("""
<style>
    /* Background Global */
    .stApp {
        background-color: #12110c;
        color: #d6d3cd;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Bar Header */
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

    /* Kartu Metrik Ringkasan Atas */
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

    /* Kartu Pemantauan Bak */
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
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #17150f;
        border: 1px solid #332d20;
        border-radius: 4px;
        padding: 5px 12px;
        font-size: 12px;
        color: #d99b26;
    }

    /* Panel Kontrol Kanan */
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
    .device-status-btn {
        background-color: #211c11;
        border: 1px solid #4a3a1d;
        border-radius: 4px;
        padding: 10px;
        text-align: center;
        font-size: 13px;
        color: #d99b26;
        font-weight: 600;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State Persisten
if 'jam_counter' not in st.session_state:
    st.session_state.jam_counter = 12  # Sesuai contoh pada Gambar 4 (12 menit berjalan)
if 'target_ka' not in st.session_state:
    st.session_state.target_ka = 14.0
if 'target_suhu' not in st.session_state:
    st.session_state.target_suhu = 42

# --- 2. HEADER ATAS (PERSIS GAMBAR 4) ---
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

# Tab Navigasi Antara Tampilan Utama Website IoT vs Skema HMI Baru
tab_utama, tab_hmi, tab_spek = st.tabs([
    "📊 Panel Monitoring 3 Bak Datar", 
    "🔄 Skema Alur Alat (3D Isometrik)", 
    "📑 Data Teknis & RAB Proposal"
])

with tab_utama:
    # --- 3. METRIK UTAMA PERSIS GAMBAR 4 PROPOSAL ---
    c1, c2, c3 = st.columns(3)
    
    # Perhitungan rata-rata kadar air simulasi
    ka1 = 25.7
    ka2 = 17.9
    ka3 = 26.4
    rata_ka = round((ka1 + ka2 + ka3) / 3, 1)

    with c1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Rata-rata kadar air seluruh bak</div>
            <div class="summary-val-large">{rata_ka} <span class="summary-val-unit">%</span></div>
            <div class="summary-footer">Target akhir {st.session_state.target_ka}%</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="summary-card">
            <div class="summary-label">Status bak</div>
            <div class="summary-val-large">0 <span class="summary-val-unit">/ 3 selesai</span></div>
            <div class="summary-footer">Semua bak dalam kondisi normal</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="summary-card">
            <div class="summary-label">Estimasi bak tersisa selesai</div>
            <div class="summary-val-large">4 <span class="summary-val-unit">jam</span> 35 <span class="summary-val-unit">mnt</span></div>
            <div class="summary-footer">Berdasarkan laju penurunan kadar air saat ini</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 4. TATA LETAK 3 BAK MONITORING & KONTROL DI KANAN ---
    col_kiri, col_kanan = st.columns([2.1, 1])

    with col_kiri:
        # Baris 3 Bak Datar
        b1, b2, b3 = st.columns(3)

        with b1:
            st.markdown("""
            <div class="bak-card">
                <div class="bak-header">
                    <span class="bak-title">Bak 1</span>
                    <span class="badge-proses">Proses</span>
                </div>
                <div class="sensor-row">🌡️ Suhu <span class="sensor-highlight">40.7°C</span> · target 42°C</div>
                <div class="sensor-row">💧 Kadar air <span class="sensor-highlight">25.7%</span> · target 14%</div>
                <div style="display:flex; gap:6px; margin-top:12px;">
                    <span class="status-pill">🌀 Blower</span>
                    <span class="status-pill">🔥 Pemanas</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with b2:
            st.markdown("""
            <div class="bak-card">
                <div class="bak-header">
                    <span class="bak-title">Bak 2</span>
                    <span class="badge-proses">Proses</span>
                </div>
                <div class="sensor-row">🌡️ Suhu <span class="sensor-highlight">45.1°C</span> · target 45°C</div>
                <div class="sensor-row">💧 Kadar air <span class="sensor-highlight">17.9%</span> · target 14%</div>
                <div style="display:flex; gap:6px; margin-top:12px;">
                    <span class="status-pill">🌀 Blower</span>
                    <span class="status-pill">🔥 Pemanas</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with b3:
            st.markdown("""
            <div class="bak-card">
                <div class="bak-header">
                    <span class="bak-title">Bak 3</span>
                    <span class="badge-proses">Proses</span>
                </div>
                <div class="sensor-row">🌡️ Suhu <span class="sensor-highlight">41.3°C</span> · target 40°C</div>
                <div class="sensor-row">💧 Kadar air <span class="sensor-highlight">26.4%</span> · target 14%</div>
                <div style="display:flex; gap:6px; margin-top:12px;">
                    <span class="status-pill">🌀 Blower</span>
                    <span class="status-pill">🔥 Pemanas</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Kartu Grafik Proses Sesuai Gambar 4
        st.markdown("""
        <div class="bak-card" style="margin-top:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-weight:700; font-size:15px; color:#f5f3ef;">Grafik proses — Bak 1</span>
                <span style="font-size:12px; color:#8c8577;">suhu (°C) &amp; kadar air (%)</span>
            </div>
            <div style="display:flex; gap:30px; margin-bottom:12px;">
                <div>
                    <div style="font-size:11px; color:#8c8577;">Suhu saat ini</div>
                    <div style="font-size:22px; font-weight:700; color:#d99b26;">40.7°C</div>
                </div>
                <div>
                    <div style="font-size:11px; color:#8c8577;">Kadar air saat ini</div>
                    <div style="font-size:22px; font-weight:700; color:#d99b26;">25.7%</div>
                </div>
                <div>
                    <div style="font-size:11px; color:#8c8577;">Lama proses berjalan</div>
                    <div style="font-size:22px; font-weight:700; color:#f5f3ef;">12 <span style="font-size:14px; font-weight:normal; color:#8c8577;">mnt</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Dataset Kurva Garis Simulasi Pengeringan
        waktu_sim = np.linspace(0, 12, 13)
        suhu_kurva = [30.0, 32.5, 34.8, 36.5, 38.0, 39.2, 40.0, 40.5, 40.8, 40.7, 40.6, 40.8, 40.7]
        ka_kurva = [27.7, 27.5, 27.2, 27.0, 26.8, 26.5, 26.3, 26.1, 26.0, 25.9, 25.8, 25.7, 25.7]
        
        df_chart = pd.DataFrame({
            "Menit": waktu_sim,
            "Suhu (°C)": suhu_kurva,
            "Kadar Air (%)": ka_kurva
        }).set_index("Menit")

        st.line_chart(df_chart, color=["#d99b26", "#4caf50"])

    with col_kanan:
        # Panel Kontrol Bak 1 Persis Gambar 4
        st.markdown("""
        <div class="control-box">
            <div class="control-title">Kontrol — Bak 1</div>
        </div>
        """, unsafe_allow_html=True)
        
        target_ka_slider = st.slider("Target kadar air (%)", 10.0, 20.0, 14.0, step=0.5)
        target_suhu_slider = st.slider("Target suhu pengering (°C)", 30, 60, 42)
        
        st.markdown("<div style='font-size:12px; color:#8c8577; margin-top:14px;'>Perangkat Aktif:</div>", unsafe_allow_html=True)
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.markdown("<div class='device-status-btn'>🌀 Blower hidup</div>", unsafe_allow_html=True)
        with c_p2:
            st.markdown("<div class='device-status-btn'>🔥 Pemanas hidup</div>", unsafe_allow_html=True)
            
        st.markdown("""
        <div style="font-size:12px; color:#8c8577; margin-top:16px;">
            <span style="color:#d99b26;">●</span> Mode: <strong>otomatis</strong>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: SKEMA ALUR HMI ISOMETRIK SESUAI GAMBAR 1 REVISI (TANPA MIKROALGA) ---
with tab_hmi:
    st.markdown("### 🗺️ Skema Integrasi Sistem Pengering Gabah SI-PADI")
    st.caption("Berdasarkan Gambar 1 Proposal Revisi: Stasiun Bioenergi, Pembersihan HE Tower, dan Sistem PLTS Darat")

    svg_isometrik = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 500" width="100%" height="100%" style="background-color: #16140e; border-radius: 8px; border: 1px solid #332d20; font-family: sans-serif;">
      
      <!-- DEFINISI GRADIENT & PANAH -->
      <defs>
        <marker id="arr-gold" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#d99b26"/>
        </marker>
        <marker id="arr-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#3fb950"/>
        </marker>
      </defs>

      <!-- 1. STASIUN BIOENERGI & PEMBERSIHAN (KIRI) -->
      <rect x="20" y="20" width="600" height="460" rx="8" fill="#1b1812" stroke="#4a3c20" stroke-width="1.5"/>
      <rect x="35" y="32" width="280" height="26" rx="4" fill="#332a17"/>
      <text x="45" y="50" fill="#f5f3ef" font-size="12" font-weight="bold">1. STASIUN BIOENERGI DAN PEMBERSIHAN</text>

      <!-- Tungku Biomassa -->
      <rect x="40" y="160" width="160" height="180" rx="6" fill="#241e15" stroke="#d99b26" stroke-width="2"/>
      <text x="120" y="195" fill="#d99b26" font-size="12" font-weight="bold" text-anchor="middle">TUNGKU BIOMASSA</text>
      <text x="120" y="215" fill="#8c8577" font-size="10" text-anchor="middle">Bahan: Batang Padi</text>
      <rect x="60" y="240" width="120" height="50" rx="4" fill="#12110c"/>
      <text x="120" y="270" fill="#ff7b72" font-size="16" font-weight="bold" text-anchor="middle">Suhu: 420°C</text>

      <!-- Cerobong Peningkat & Filter HEPA Ganda -->
      <rect x="220" y="80" width="100" height="150" rx="4" fill="#241e15" stroke="#8c8577"/>
      <text x="270" y="105" fill="#f5f3ef" font-size="10" font-weight="bold" text-anchor="middle">CEROBONG PENINGKAT</text>
      <text x="270" y="120" fill="#8c8577" font-size="9" text-anchor="middle">(Heat Riser)</text>
      <line x1="220" y1="135" x2="320" y2="135" stroke="#57431e" stroke-width="2"/>
      <text x="270" y="155" fill="#d99b26" font-size="9" text-anchor="middle">Coarse Filter (Kasar)</text>
      <text x="270" y="175" fill="#3fb950" font-size="9" text-anchor="middle">HEPA &amp; Gas Filter</text>
      
      <!-- Pipa Aliran Gas Buang Bersih -->
      <path d="M 270 80 L 270 60 L 370 60" stroke="#3fb950" stroke-width="3" fill="none" marker-end="url(#arr-green)"/>
      <text x="350" y="52" fill="#3fb950" font-size="9">Aliran Gas Buang Bersih</text>

      <!-- Menara Penukar Panas (HE Tower Coil) -->
      <rect x="340" y="100" width="110" height="240" rx="6" fill="#1e221b" stroke="#3fb950" stroke-width="2"/>
      <text x="395" y="125" fill="#3fb950" font-size="11" font-weight="bold" text-anchor="middle">HEAT EXCHANGER</text>
      <text x="395" y="142" fill="#8c8577" font-size="9" text-anchor="middle">Menara Koil Penukar</text>
      <circle cx="395" cy="180" r="24" fill="#12110c" stroke="#3fb950"/>
      <text x="395" y="185" fill="#3fb950" font-size="12" font-weight="bold" text-anchor="middle">85%</text>
      <text x="395" y="240" fill="#8c8577" font-size="9" text-anchor="middle">Asupan Udara Bersih</text>
      <text x="395" y="255" fill="#f5f3ef" font-size="9" text-anchor="middle">Dipanaskan Bersih</text>

      <!-- Rumah Pengering Gabah Bak Datar Bertingkat -->
      <rect x="470" y="80" width="130" height="280" rx="6" fill="#241e15" stroke="#d99b26" stroke-width="2"/>
      <text x="535" y="110" fill="#d99b26" font-size="11" font-weight="bold" text-anchor="middle">RUMAH PENGERING</text>
      <text x="535" y="125" fill="#8c8577" font-size="9" text-anchor="middle">Rak Gabah Bertingkat</text>
      
      <!-- 3 Bak di Dalam Rumah Pengering -->
      <rect x="485" y="145" width="100" height="40" rx="3" fill="#12110c" stroke="#57431e"/>
      <text x="535" y="165" fill="#f5f3ef" font-size="10" text-anchor="middle">Bak 1: 25.7%</text>
      <rect x="485" y="195" width="100" height="40" rx="3" fill="#12110c" stroke="#57431e"/>
      <text x="535" y="215" fill="#f5f3ef" font-size="10" text-anchor="middle">Bak 2: 17.9%</text>
      <rect x="485" y="245" width="100" height="40" rx="3" fill="#12110c" stroke="#57431e"/>
      <text x="535" y="265" fill="#f5f3ef" font-size="10" text-anchor="middle">Bak 3: 26.4%</text>

      <path d="M 450 220 L 470 220" stroke="#d99b26" stroke-width="4" fill="none" marker-end="url(#arr-gold)"/>

      <!-- 2. SISTEM ENERGI SURYA PLTS DARAT (KANAN) -->
      <rect x="640" y="20" width="340" height="460" rx="8" fill="#1b1812" stroke="#4a3c20" stroke-width="1.5"/>
      <rect x="655" y="32" width="240" height="26" rx="4" fill="#332a17"/>
      <text x="665" y="50" fill="#f5f3ef" font-size="12" font-weight="bold">2. SISTEM ENERGI SURYA (PLTS)</text>

      <!-- Panel Surya Darat -->
      <rect x="665" y="80" width="290" height="110" rx="6" fill="#172230" stroke="#388bfd" stroke-width="2"/>
      <text x="810" y="125" fill="#58a6ff" font-size="14" font-weight="bold" text-anchor="middle">☀️ PANEL SURYA DARAT</text>
      <text x="810" y="148" fill="#8c8577" font-size="11" text-anchor="middle">Kapasitas: 4.000 Wp</text>

      <!-- Arus DC & Solar Charge Controller -->
      <path d="M 810 190 L 810 220" stroke="#d99b26" stroke-width="3" fill="none" marker-end="url(#arr-gold)"/>
      <rect x="710" y="220" width="200" height="60" rx="6" fill="#241e15" stroke="#d99b26"/>
      <text x="810" y="245" fill="#d99b26" font-size="11" font-weight="bold" text-anchor="middle">SOLAR CHARGE CONTROLLER</text>
      <text x="810" y="265" fill="#3fb950" font-size="10" text-anchor="middle">MPPT Inverter Aktif</text>

      <!-- Baterai Penyimpanan -->
      <path d="M 810 280 L 810 310" stroke="#d99b26" stroke-width="3" fill="none" marker-end="url(#arr-gold)"/>
      <rect x="710" y="310" width="200" height="60" rx="6" fill="#241e15" stroke="#3fb950"/>
      <text x="810" y="335" fill="#3fb950" font-size="11" font-weight="bold" text-anchor="middle">BATERAI PENYIMPANAN</text>
      <text x="810" y="355" fill="#8c8577" font-size="10" text-anchor="middle">Storage Cadangan Mandiri</text>

      <!-- Beban Suplai Alat -->
      <rect x="665" y="390" width="290" height="70" rx="6" fill="#12110c" stroke="#332d20"/>
      <text x="680" y="415" fill="#8c8577" font-size="10">⚡ Penyuplai Kebutuhan Listrik:</text>
      <text x="680" y="433" fill="#f5f3ef" font-size="10">• Blower Sirkulasi Udara Pengering</text>
      <text x="680" y="449" fill="#f5f3ef" font-size="10">• Perangkat Elektronik &amp; Gateway IoT</text>

    </svg>
    """
    st.components.v1.html(svg_isometrik, height=520)

# --- TAB 3: SPESIFIKASI TEKNIS & RAB PROPOSAL REVISI (RP 220 JUTA) ---
with tab_spek:
    st.markdown("### 📋 Spesifikasi Teknis & Rencana Anggaran Biaya Revisi")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("""
        **Spesifikasi Teknis Alat SI-PADI:**
        - **Dimensi Rumah Pengering:** $\\pm 6\\text{ m} \\times 4\\text{ m} \\times 3\\text{ m}$
        - **Kapasitas Produksi:** $\\pm 1\\text{ Ton}$ gabah segar per siklus pengeringan (18–24 jam)
        - **Kadar Air Awal $\\rightarrow$ Akhir:** $27.72\\%$ (basis basah) $\\rightarrow 14.0\\%$ (Standar Mutu SNI 6128:2020)
        - **Sumber Daya:** Pembangkit Listrik Tenaga Surya (PLTS) Hybrid $\\pm 4.000\\text{ Wp}$ & Tungku Biomassa Batang Padi
        - **Tingkat Kesiapan Teknologi:** TKT 6–7 (Prototipe teruji operasional lapangan)
        """)
    with col_d2:
        st.markdown("""
        **Rencana Anggaran Biaya (RAB) Revisi:**
        - **Total RAB Diusulkan:** **Rp 220.000.000,-** *(Maksimal Rp 250.000.000,-)*
        - **Komponen Utama:** Kolektor Surya, Rumah Pengering Galvanis, Tungku Biomassa Cor Beton, Blower, Pipa Stainless Steel, Filter HEPA & Coarse
        - **Lokasi Implementasi:** Pusat Organik PUSAKA BLORA, Desa Sidorejo, Kec. Kedungtuban, Kab. Blora
        - **Mitra Lapangan:** PT Pertamina EP Cepu Field Cepu
        """)

# --- 5. FOOTER RESMI ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #716b5f; font-size: 12px; line-height: 1.6;">
    <strong>SI-PADI — Kompetisi Inovasi Teknologi dan Energi Program PFsains 2026</strong><br>
    Ketua Tim: Prof. Dr. Ir. Widayat, S.T., M.T., IPM., ASEAN Eng. (Universitas Diponegoro)<br>
    Anggota: Ir. Ali Mutakin, S.Kom. · Yusron Mahendra Diwiyanto, S.T.<br>
    Pusat Organik PUSAKA BLORA · Pertamina Foundation
</div>
""", unsafe_allow_html=True)

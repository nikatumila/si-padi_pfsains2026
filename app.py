import streamlit as st
import pandas as pd
import numpy as np

# --- 1. KONFIGURASI HALAMAN INDUSTRIAL DARK ---
st.set_page_config(
    page_title="SI-PADI — Pusat Kendali & Pemantauan IoT",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Industrial Dark UI sesuai Gambar 5 Proposal
st.markdown("""
<style>
    /* Background Dasar Web */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Box Header */
    .header-box {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 26px;
        font-weight: 700;
        color: #f0883e;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .header-subtitle {
        font-size: 14px;
        color: #8b949e;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .metric-label {
        font-size: 13px;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #58a6ff;
    }
    .metric-unit {
        font-size: 15px;
        color: #8b949e;
        font-weight: normal;
    }

    /* Station Containers */
    .station-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .station-title {
        font-size: 16px;
        font-weight: 600;
        color: #f0883e;
        border-bottom: 1px solid #21262d;
        padding-bottom: 8px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State Penyimpanan Data
if 'history' not in st.session_state:
    st.session_state.history = []
if 'jam_counter' not in st.session_state:
    st.session_state.jam_counter = 0

# --- 2. SIDEBAR KONTROL SIMULASI ---
st.sidebar.markdown("### ⚙️ Kontrol Parameter Simulasi")
st.sidebar.caption("Data Generator Kinetika Pengeringan SI-PADI")

kondisi_cuaca = st.sidebar.selectbox(
    "Sumber Pasokan Energi:",
    ["Surya Penuh (Cerah)", "Hibrida (Mendung)", "Biomassa Penuh (Hujan/Malam)"]
)

target_kadar_air = st.sidebar.slider("Target Akhir Kadar Air Gabah (%)", 12.0, 16.0, 14.0, step=0.5)
suhu_setpoint = st.sidebar.slider("Setpoint Suhu Ruang Pengering (°C)", 35, 60, 50)
kapasitas_gabah = st.sidebar.selectbox("Muatan Gabah Basah:", ["500 kg", "1000 kg (1 Ton - Full Batch)"])

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    btn_step = st.sidebar.button("⏱️ +1 Jam Proses")
with col_btn2:
    if st.sidebar.button("🔄 Reset"):
        st.session_state.history = []
        st.session_state.jam_counter = 0
        st.rerun()

# Logika Pemodelan Kinetika Berdasarkan Sumber Daya
if kondisi_cuaca == "Surya Penuh (Cerah)":
    status_energi = "PLTS PRIMER & BIOMASSA STANDBY"
    suhu_tungku = 180 + np.random.uniform(-5, 5)
    efisiensi_he = 88.5
    daya_plts = 3850 + np.random.uniform(-100, 100)
    daya_baterai = min(100.0, 92.0 + st.session_state.jam_counter * 0.5)
    bio_co2 = 65.0 + np.random.uniform(-2, 2)
elif kondisi_cuaca == "Hibrida (Mendung)":
    status_energi = "HIBRIDA PLTS (50%) & BIOMASSA (50%)"
    suhu_tungku = 320 + np.random.uniform(-8, 8)
    efisiensi_he = 84.0
    daya_plts = 1800 + np.random.uniform(-80, 80)
    daya_baterai = max(50.0, 85.0 - st.session_state.jam_counter * 1.5)
    bio_co2 = 82.0 + np.random.uniform(-2, 2)
else:
    status_energi = "BIOMASSA TOTAL (100%) - ZERO CARBON EMISSION"
    suhu_tungku = 440 + np.random.uniform(-12, 12)
    efisiensi_he = 81.5
    daya_plts = 0.0
    daya_baterai = max(40.0, 95.0 - st.session_state.jam_counter * 3.2)
    bio_co2 = 91.5 + np.random.uniform(-1, 1)

# Rumus Penurunan Kadar Air: 27.72% basis basah menuju target (14% SNI) dalam 24 jam
ka_mulai = 27.72
laju_pengurangan = (ka_mulai - target_kadar_air) / 24.0
current_ka = max(target_kadar_air, ka_mulai - (st.session_state.jam_counter * laju_pengurangan) + np.random.uniform(-0.15, 0.15))

if btn_step:
    st.session_state.jam_counter += 1
    st.session_state.history.append({
        "Jam": st.session_state.jam_counter,
        "Kadar Air (%)": round(current_ka, 2),
        "Suhu Pengering (°C)": suhu_setpoint + np.random.uniform(-1.2, 1.2),
        "Suhu Tungku (°C)": round(suhu_tungku, 1),
        "Baterai PLTS (%)": round(daya_baterai, 1),
        "Daya PLTS (W)": round(daya_plts, 0)
    })

# --- 3. HEADER RESMI ---
st.markdown(f"""
<div class="header-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div class="header-title">SI-PADI: Pusat Kendali & Pemantauan IoT</div>
            <div class="header-subtitle">Unit Pengering Padi Surya Terintegrasi Biomassa & Bio-Capture · Mitra: PUSAKA BLORA</div>
        </div>
        <div style="text-align:right;">
            <span style="background-color: #1f6feb; color: #ffffff; padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">
                🔬 DIGITAL TWIN SIMULATION
            </span>
            <div style="color:#8b949e; font-size:11px; margin-top:5px;">Mode: {status_energi}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# TABS UTAMA (4 TAB LENGKAP)
tab_dash, tab_hmi, tab_spek, tab_ekonomi = st.tabs([
    "📊 Dashboard Monitoring IoT", 
    "🔄 HMI Skema Alur Digital Twin", 
    "📑 Spesifikasi & SOP",
    "💰 Kelayakan Finansial & Tekno-Ekonomi"
])

# ====================================================================
# TAB 1: DASHBOARD MONITORING TIGA STASIUN (GAMBAR 5 PROPOSAL)
# ====================================================================
with tab_dash:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Kadar Air Gabah Rata-Rata</div>
            <div class="metric-value" style="color:#3fb950;">{current_ka:.2f}<span class="metric-unit"> %</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Suhu Ruang Pengering</div>
            <div class="metric-value">{suhu_setpoint:.1f}<span class="metric-unit"> °C</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Daya Output PLTS</div>
            <div class="metric-value" style="color:#f0883e;">{daya_plts:.0f}<span class="metric-unit"> Wp</span></div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">CO₂ Bio-Capture (Alga)</div>
            <div class="metric-value" style="color:#58a6ff;">{bio_co2:.1f}<span class="metric-unit"> %</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        st.markdown("""
        <div class="station-card">
            <div class="station-title">🔥 1. Stasiun Bioenergi & Gas Cleaning</div>
        """, unsafe_allow_html=True)
        st.write(f"**Suhu Ruang Bakar:** `{suhu_tungku:.1f} °C`")
        st.write(f"**Filter Kasar & HEPA Gas:** `Normal (Terpasang)`")
        st.write(f"**Efisiensi Heat Exchanger:** `{efisiensi_he}%`")
        st.write(f"**Sisa Gas Buang:** `Teralirkan ke Bio-Capture`")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_s2:
        st.markdown("""
        <div class="station-card">
            <div class="station-title">☀️ 2. Sistem PLTS & Kelistrikan</div>
        """, unsafe_allow_html=True)
        st.write(f"**Kapasitas Panel:** `4.000 Wp (Hybrid On/Off-Grid)`")
        st.write(f"**Penyimpanan Baterai:** `{daya_baterai:.1f} %`")
        st.write(f"**Blower Udara Panas:** `Aktif (100% DC Inverter)`")
        st.write(f"**Solar Charge Controller:** `MPPT Normal`")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_s3:
        st.markdown("""
        <div class="station-card">
            <div class="station-title">🌾 3. Pengering Gabah & Kolam Alga</div>
        """, unsafe_allow_html=True)
        st.write(f"**Kapasitas Batch:** `{kapasitas_gabah}`")
        st.write(f"**Waktu Siklus Berjalan:** `{st.session_state.jam_counter} Jam / 24 Jam`")
        st.write(f"**Target Mutu:** `SNI 6128:2020 (KA 14%)`")
        st.write(f"**Kolam Mikroalga:** `Fotobioreaktor Berputar Aktif`")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 📈 Tren Penurunan Kadar Air & Keseimbangan Termal")
    if st.session_state.history:
        df_hist = pd.DataFrame(st.session_state.history).set_index("Jam")
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Penurunan Kadar Air Gabah (%) per Jam")
            st.line_chart(df_hist[["Kadar Air (%)"]], color="#3fb950")
        with g2:
            st.caption("Dinamika Suhu (°C): Tungku Biomassa vs Ruang Pengering")
            st.line_chart(df_hist[["Suhu Tungku (°C)", "Suhu Pengering (°C)"]], color=["#f0883e", "#58a6ff"])
            
        st.download_button(
            label="📥 Unduh Data Log Pengeringan (.CSV)",
            data=df_hist.to_csv().encode('utf-8'),
            file_name=f"sipadi_log_batch_{st.session_state.jam_counter}jam.csv",
            mime="text/csv"
        )
    else:
        st.info("💡 Tekan tombol '⏱️ +1 Jam Proses' pada panel sidebar sebelah kiri untuk melihat simulasi dinamis grafik penurunan kadar air.")

# ====================================================================
# TAB 2: HMI DIGITAL TWIN (GAMBAR 1 PROPOSAL)
# ====================================================================
with tab_hmi:
    st.markdown("### 🗺️ Skema Digital Twin Alur Termal & Sirkular Karbon")
    st.caption("Visualisasi dinamis integrasi Bioenergy, PLTS, Heat Exchanger, Ruang Pengering, dan Bak Mikroalga")

    svg_hmi = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 400" width="100%" height="100%" style="background-color: #161b22; border-radius: 10px; border: 1px solid #30363d; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">
      <defs>
        <marker id="arrow-orange" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#f0883e"/>
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#3fb950"/>
        </marker>
        <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#58a6ff"/>
        </marker>
      </defs>

      <!-- 1. TUNGKU BIOMASSA -->
      <rect x="30" y="80" width="160" height="150" rx="8" fill="#21262d" stroke="#f0883e" stroke-width="2"/>
      <text x="110" y="110" fill="#f0883e" font-size="13" font-weight="bold" text-anchor="middle">🔥 TUNGKU BIOMASSA</text>
      <text x="110" y="130" fill="#8b949e" font-size="11" text-anchor="middle">Bahan: Batang Padi</text>
      <rect x="50" y="150" width="120" height="50" rx="4" fill="#0d1117" stroke="#30363d"/>
      <text x="110" y="180" fill="#ff7b72" font-size="18" font-weight="bold" text-anchor="middle">{suhu_tungku:.0f} °C</text>

      <!-- FILTER & GAS DUCT -->
      <path d="M 190 140 L 250 140" stroke="#f0883e" stroke-width="4" fill="none" marker-end="url(#arrow-orange)"/>
      <rect x="250" y="90" width="90" height="100" rx="6" fill="#21262d" stroke="#8b949e" stroke-width="1.5"/>
      <text x="295" y="130" fill="#e6edf3" font-size="11" font-weight="bold" text-anchor="middle">FILTER GAS</text>
      <text x="295" y="150" fill="#3fb950" font-size="10" text-anchor="middle">HEPA & Coarse</text>

      <!-- 2. HEAT EXCHANGER HIBRIDA -->
      <path d="M 340 140 L 390 140" stroke="#f0883e" stroke-width="4" fill="none" marker-end="url(#arrow-orange)"/>
      <circle cx="440" cy="140" r="50" fill="#1f242c" stroke="#58a6ff" stroke-width="3"/>
      <text x="440" y="135" fill="#58a6ff" font-size="12" font-weight="bold" text-anchor="middle">HEAT</text>
      <text x="440" y="152" fill="#58a6ff" font-size="12" font-weight="bold" text-anchor="middle">EXCHANGER</text>

      <!-- UDARA BERSIH PANAS KE PENGERING -->
      <path d="M 490 140 L 570 140" stroke="#f0883e" stroke-width="5" fill="none" marker-end="url(#arrow-orange)"/>
      <text x="530" y="130" fill="#f0883e" font-size="10" text-anchor="middle">Udara Bersih</text>

      <!-- 3. RUMAH PENGERING GABAH -->
      <rect x="580" y="60" width="180" height="170" rx="8" fill="#1b2a1e" stroke="#3fb950" stroke-width="2"/>
      <text x="670" y="90" fill="#3fb950" font-size="14" font-weight="bold" text-anchor="middle">🌾 RUMAH PENGERING</text>
      <text x="670" y="110" fill="#8b949e" font-size="11" text-anchor="middle">Dimensi: 6m × 4m × 3m</text>
      <rect x="600" y="125" width="140" height="85" rx="4" fill="#0d1117" stroke="#238636"/>
      <text x="670" y="150" fill="#58a6ff" font-size="13" font-weight="bold" text-anchor="middle">Suhu: {suhu_setpoint:.1f} °C</text>
      <text x="670" y="175" fill="#3fb950" font-size="17" font-weight="bold" text-anchor="middle">KA: {current_ka:.2f} %</text>
      <text x="670" y="195" fill="#8b949e" font-size="10" text-anchor="middle">Batch: {kapasitas_gabah}</text>

      <!-- GAS BUANG CO2 KE STORAGE & KOLAM ALGA -->
      <path d="M 440 190 L 440 280 L 550 280" stroke="#8b949e" stroke-dasharray="4" stroke-width="3" fill="none" marker-end="url(#arrow-blue)"/>
      <rect x="550" y="250" width="100" height="60" rx="4" fill="#21262d" stroke="#8b949e" stroke-width="1.5"/>
      <text x="600" y="275" fill="#e6edf3" font-size="10" font-weight="bold" text-anchor="middle">STORAGE DRUM</text>
      <text x="600" y="295" fill="#8b949e" font-size="9" text-anchor="middle">Gas Buang Sisa</text>

      <path d="M 650 280 L 710 280" stroke="#3fb950" stroke-width="3" fill="none" marker-end="url(#arrow-green)"/>

      <!-- 4. KOLAM MIKROALGA -->
      <rect x="720" y="240" width="190" height="90" rx="8" fill="#063222" stroke="#2ea043" stroke-width="2"/>
      <text x="815" y="265" fill="#3fb950" font-size="12" font-weight="bold" text-anchor="middle">🧪 BAK MIKROALGA</text>
      <text x="815" y="285" fill="#7ee787" font-size="11" text-anchor="middle">Bio-Capture: {bio_co2:.1f}%</text>
      <text x="815" y="310" fill="#8b949e" font-size="10" text-anchor="middle">Produksi Biomassa Nilai Tambah</text>

      <!-- 5. PLTS ENERGY SYSTEM DI BAWAH -->
      <rect x="50" y="260" width="220" height="90" rx="8" fill="#1f2328" stroke="#d29922" stroke-width="2"/>
      <text x="160" y="285" fill="#d29922" font-size="12" font-weight="bold" text-anchor="middle">☀️ PLTS SURYA HYBRID</text>
      <text x="160" y="308" fill="#e6edf3" font-size="11" text-anchor="middle">Daya Suplai: {daya_plts:.0f} Wp</text>
      <text x="160" y="328" fill="#3fb950" font-size="11" text-anchor="middle">Baterai: {daya_baterai:.1f}%</text>
    </svg>
    """
    st.components.v1.html(svg_hmi, height=430)

# ====================================================================
# TAB 3: SPESIFIKASI TEKNIK & SOP
# ====================================================================
with tab_spek:
    st.markdown("### 📋 Ringkasan Teknis Proyek (PFsains 2026)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("""
        **Spesifikasi Fisik & Kapasitas:**
        - **Dimensi Rumah Pengering:** $\\pm 6\\text{ m} \\times 4\\text{ m} \\times 3\\text{ m}$
        - **Kapasitas Batch:** $\\pm 1\\text{ Ton}$ gabah segar per siklus pengeringan (18–24 jam)
        - **Material:** Rangka baja ringan galvanis, dinding polikarbonat UV-protected, lantai stainless steel
        - **Tingkat Kesiapan Teknologi:** TKT 6–7 (Prototipe teruji di lingkungan operasional nyata)
        """)
    with col_t2:
        st.markdown("""
        **Kemitraan & Standar:**
        - **Lokasi Implementasi:** Pusat Organik PUSAKA BLORA, Desa Sidorejo, Kec. Kedungtuban, Kab. Blora
        - **Dukungan Kemitraan:** PT Pertamina EP Cepu Field Cepu & Pertamina Foundation
        - **Standar Output:** SNI 6128:2020 (Kadar air aman simpan $\\leq 14\\%$)
        - **SOP Perawatan:** Pembersihan panel berkala, kalibrasi sensor per 6 bulan
        """)

# ====================================================================
# TAB 4: KELAYAKAN FINANSIAL & TEKNO-EKONOMI (BAB III PROPOSAL)
# ====================================================================
with tab_ekonomi:
    st.markdown("### 💰 Analisis Kelayakan Finansial & Tekno-Ekonomi")
    st.caption("Parameter kelayakan investasi alat pengering SI-PADI berdasarkan Bab 3.2 Proposal (Diskonto 12%, Umur Alat 10 Tahun)")
    
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Capital Investment</div>
            <div class="metric-value">USD 2,550</div>
        </div>
        """, unsafe_allow_html=True)
    with e2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Net Present Value (NPV)</div>
            <div class="metric-value" style="color:#3fb950;">USD 8,563</div>
        </div>
        """, unsafe_allow_html=True)
    with e3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Payback Period</div>
            <div class="metric-value" style="color:#f0883e;">±1.6 <span class="metric-unit">Tahun</span></div>
        </div>
        """, unsafe_allow_html=True)
    with e4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Margin Nilai Tambah</div>
            <div class="metric-value" style="color:#58a6ff;">+33.3 <span class="metric-unit">%</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    - **Harga Gabah Segar (Input):** USD 0,36 / kg
    - **Harga Gabah Kering (Output):** USD 0,48 / kg
    - **Evaluasi Keekonomian:** Investasi dinyatakan **sangat layak (feasible)** karena periode pengembalian modal (1,6 tahun) jauh lebih singkat dibandingkan estimasi umur ekonomis alat (10 tahun).
    - **Dampak Karbon (ESG):** Pemanfaatan biomassa limbah batang padi bersifat netral karbon (*carbon-neutral*), sementara emisi gas buangnya diserap (*bio-capture*) oleh kolam mikroalga.
    """)

# --- 5. FOOTER IDENTITAS RESMI TIM PENGUSUL ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8b949e; font-size: 12px; line-height: 1.6;">
    <strong>SI-PADI — Program Kompetisi Inovasi Teknologi dan Energi PFsains 2026</strong><br>
    Ketua Tim: Prof. Dr. Ir. Widayat, S.T., M.T., IPM., ASEAN Eng. (Universitas Diponegoro)<br>
    Tim Peneliti: Ir. Ali Mutakin, S.Kom. · Yusron Mahendra Diwiyanto, S.T.<br>
    Mitra Lapangan: Pusat Organik PUSAKA BLORA & PT Pertamina EP Cepu Field Cepu
</div>
""", unsafe_allow_html=True)

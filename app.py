import streamlit as st
import pandas as pd
import numpy as np
import math
import random

# --- 1. KONFIGURASI WEB DASHBOARD ---
st.set_page_config(page_title="Panel Monitoring — Pengering Gabah Padi", page_icon="🌾", layout="wide")

# Mengunci judul utama sesuai dengan dokumen proposal Anda
st.title("🌾 Panel Monitoring — Pengering Gabah Padi")
st.caption("Unit pengering bak datar · 3 bak aktif · data disimulasikan untuk demo")
st.markdown("---")

# Inisialisasi data history untuk merekam pergerakan grafik saat Anda klik-klik
if 'history' not in st.session_state:
    st.session_state.history = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'jam_counter' not in st.session_state:
    st.session_state.jam_counter = 0

# --- 2. SIDEBAR KONTROL UTAMA (PANEL KLIK-KLIK DI SINI) ---
st.sidebar.header("🎛️ Panel Kontrol Alat")

mode_cuaca = st.sidebar.selectbox(
    "1. Pilih Kondisi Lingkungan:",
    ["☀️ Cerah Benderang", "☁️ Mendung Berawan", "🌧️ Hujan / Malam Hari"]
)

# Slider interaktif untuk mematangkan data fisik
suhu_ruang_set = st.sidebar.slider("2. Set Suhu Ruang Pengering (°C)", 20, 65, 50)
ka_input = st.sidebar.slider("3. Set Kadar Air Gabah Saat Ini (%)", 10.0, 30.0, 22.0)

col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    submit_data = st.sidebar.button("💾 Kirim Data IoT")
with col_b2:
    if st.sidebar.button("🔄 Reset Jalur"):
        st.session_state.history = []
        st.session_state.logs = []
        st.session_state.jam_counter = 0
        st.rerun()

# --- 3. LOGIKA PROSES & SIMULASI HARDWARE ---
if mode_cuaca == "☀️ Cerah Benderang":
    warna_cuaca = "#2e7d32"
    teks_cuaca = "☀️ CERAH - PLTS MENYUPLAI DAYA PENUH"
    suhu_tungku = 280.0 + random.uniform(-5, 5)
    baterai = min(100.0, 85.0 + st.session_state.jam_counter * 1.5)
elif mode_cuaca == "☁️ Mendung Berawan":
    warna_cuaca = "#f57c00"
    teks_cuaca = "☁️ MENDUNG - SUPLAI PLTS TURUN, BIOMASSA MENINGKAT"
    suhu_tungku = 360.0 + random.uniform(-10, 10)
    baterai = max(55.0, 90.0 - st.session_state.jam_counter * 1.2)
else:
    warna_cuaca = "#c62828"
    teks_cuaca = "🌧️ HUJAN/MALAM - SISTEM TOTAL HIBRIDA BIOMASSA AKTIF"
    suhu_tungku = 450.0 + random.uniform(-15, 15)
    baterai = max(35.0, 100.0 - st.session_state.jam_counter * 3.5)

co2_capture = 78.5 + random.uniform(-1.5, 1.5) if suhu_tungku > 25 else 0.0

# Variasi kadar air untuk simulasi 3 bak aktif pengering bak datar
ka_bak1 = ka_input
ka_bak2 = max(10.0, ka_input - 0.5 + random.uniform(-0.1, 0.1))
ka_bak3 = max(10.0, ka_input + 0.4 + random.uniform(-0.1, 0.1))

# Merekam data ke riwayat grafik jika tombol kirim data diklik
if submit_data:
    st.session_state.jam_counter += 1
    st.session_state.history.append({
        "Jam": st.session_state.jam_counter,
        "Suhu Ruang (°C)": suhu_ruang_set,
        "Bak 1 (%)": round(ka_bak1, 2),
        "Bak 2 (%)": round(ka_bak2, 2),
        "Bak 3 (%)": round(ka_bak3, 2),
        "Baterai (%)": round(baterai, 1)
    })
    
    # Log peringatan otomatis responsif terhadap klik-klik Anda
    if baterai < 45.0:
        st.session_state.logs.append(f"⚠️ [Log] Baterai PLTS Kritis: {baterai:.1f}% pada simulasi data ke-{st.session_state.jam_counter}")
    if suhu_ruang_set > 55.0:
        st.session_state.logs.append(f"🚨 [ALARM] Suhu Ruang Overheat ({suhu_ruang_set}°C)! Kipas otomatis maksimal.")

# --- 4. PEMBAGIAN KELOMPOK 2 HALAMAN (TABS) ---
tab1, tab2 = st.tabs(["🏭 Halaman 1: Skema Alat HMI", "📊 Halaman 2: Dashboard Monitoring"])

# ==========================================
# HALAMAN 1: SKEMA ALAT HMI INTERAKTIF
# ==========================================
with tab1:
    st.markdown("### 🗺️ Interaktif Digital Twin — Aliran Termal & Elektrikal")
    st.write("Gunakan panel kontrol di sebelah kiri untuk mengubah kondisi alat secara langsung.")
    
    # Template Gambar Skema Integrasi Proposal Anda yang Diubah Menjadi Hidup
    svg_template = f"""
    <svg xmlns="http://w3.org" viewBox="0 0 800 360" width="100%" height="100%" style="background-color: #1e1e1e; font-family: sans-serif; border-radius: 8px;">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#ff9800"/>
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#4caf50"/>
        </marker>
      </defs>

      <!-- BAR STATUS LINGKUNGAN -->
      <rect x="0" y="0" width="800" height="40" fill="{warna_cuaca}"/>
      <text x="400" y="25" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">STATUS OPERASIONAL: {teks_cuaca}</text>

      <!-- JALUR PIPA GAS DAN UDARA -->
      <path d="M 160 160 L 260 160" stroke="#ff5722" stroke-width="6" fill="none" marker-end="url(#arrow)" />
      <path d="M 380 130 L 480 130" stroke="#ff9800" stroke-width="6" fill="none" marker-end="url(#arrow)" />
      <path d="M 320 210 L 320 280 L 520 280" stroke="#4caf50" stroke-width="6" fill="none" marker-end="url(#arrow-green)" />

      <!-- KOMPONEN 1: TUNGKU BIOMASSA -->
      <rect x="20" y="90" width="140" height="140" rx="10" fill="#3e2723" stroke="#ff5722" stroke-width="3" />
      <text x="90" y="125" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">🔥 TUNGKU BIOMASSA</text>
      <text x="90" y="145" fill="#d7ccc8" font-size="10" text-anchor="middle">Limbah Batang Padi</text>
      <rect x="40" y="170" width="100" height="40" rx="5" fill="#212121" />
      <text x="90" y="195" fill="#ff5722" font-size="16" font-weight="bold" text-anchor="middle">{suhu_tungku:.0f}°C</text>

      <!-- KOMPONEN 2: PENUKAR PANAS (HEAT EXCHANGER) -->
      <rect x="260" y="90" width="120" height="120" rx="60" fill="#0d47a1" stroke="#29b6f6" stroke-width="3" />
      <text x="320" y="140" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">🔄 EXCHANGER</text>
      <text x="320" y="165" fill="#81d4fa" font-size="12" font-weight="bold" text-anchor="middle">Efisiensi: 85%</text>

      <!-- KOMPONEN 3: RUMAH PENGERING GABAH -->
      <polygon points="480,100 560,50 640,100 640,230 480,230" fill="#1b5e20" stroke="#4caf50" stroke-width="3" />
      <text x="560" y="125" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">🌾 RUMAH PENGERING</text>
      
      <rect x="500" y="150" width="120" height="60" rx="5" fill="#212121" />
      <text x="560" y="170" fill="#4caf50" font-size="12" font-weight="bold" text-anchor="middle">Suhu: {suhu_ruang_set:.1f}°C</text>
      <text x="560" y="195" fill="#29b6f6" font-size="12" font-weight="bold" text-anchor="middle">Rata2 KA: {ka_input:.1f}%</text>

      <!-- KOMPONEN 4: BAK MIKROALGA (BIO-CAPTURE CO2) -->
      <rect x="520" y="250" width="230" height="60" rx="8" fill="#004d40" stroke="#00b0ff" stroke-width="2" />
      <text x="635" y="275" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">🧪 BAK MIKROALGA</text>
      <text x="635" y="295" fill="#80cbc4" font-size="11" text-anchor="middle">Bio-Capture CO₂: {co2_capture:.1f}%</text>
    </svg>
    """
    st.components.v1.html(svg_template, height=380)

# ==========================================
# HALAMAN 2: DASHBOARD MONITORING DATA
# ==========================================
with tab2:
    st.markdown("### 📊 Pusat Kontrol Analitik & Tren Proses")
    
    # 3 Bak Aktif Pemantauan Angka Digital
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Suhu Udara Masuk", f"{suhu_ruang_set} °C")
    col2.metric("💧 Kadar Air Bak 1", f"{ka_bak1:.2f}%", "Aktif")
    col3.metric("💧 Kadar Air Bak 2", f"{ka_bak2:.2f}%", "Aktif")
    col4.metric("💧 Kadar Air Bak 3", f"{ka_bak3:.2f}%", "Aktif")
    
    st.markdown("---")
    
    # Grafik Proses Kombinasi Suhu & Kadar Air
    st.markdown("#### Grafik proses suhu (°C) & kadar air (%)")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history).set_index("Jam")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("**Grafik Kadar Air (%) Kelompok Bak Datar**")
            st.line_chart(df[["Bak 1 (%)", "Bak 2 (%)", "Bak 3 (%)"]], color=["#2E7D32", "#1565C0", "#E65100"])
        with col_g2:
            st.write("**Grafik Stabilitas Suhu Kamar vs Baterai PLTS**")
            st.line_chart(df[["Suhu Ruang (°C)", "Baterai (%)"]])
    else:
        st.info("Belum ada data terekam. Silakan klik tombol '💾 Kirim Data IoT' di panel kiri beberapa kali untuk mulai menggambar grafik proses.")

    st.markdown("---")

    # Log Peringatan Sistem Infografis
    st.markdown(f"#### 📋 Log peringatan ({len(st.session_state.logs)} entri)")
    if st.session_state.logs:
        for log in reversed(st.session_state.logs):
            st.error(log)
    else:
        st.info("Log peringatan 0 entri — Seluruh subsistem berjalan normal")

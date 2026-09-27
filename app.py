# ------------------------------------------------------------------------------
# TAB 2: HMI DIGITAL TWIN (TATA LETAK PRESISI & ANTI-TUMPANG TINDIH)
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

      <!-- Jalur Emisi Bersih Terfiltrasi (Dinaikkan agar tidak menabrak kotak) -->
      <path d="M 235 110 L 235 75 L 360 75" stroke="#3fb950" stroke-width="2.5" fill="none" marker-end="url(#arrow-green)"/>
      <text x="370" y="79" fill="#3fb950" font-size="10" font-weight="600">Aliran Emisi Bersih Terfiltrasi</text>

      <!-- Tungku Biomassa Cor Beton -->
      <rect x="40" y="170" width="130" height="200" rx="6" fill="#1d202d" stroke="#d19a38" stroke-width="2"/>
      <text x="105" y="205" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">TUNGKU BIOMASSA</text>
      <text x="105" y="225" fill="#8890a1" font-size="10" text-anchor="middle">Limbah Batang Padi</text>
      <rect x="52" y="245" width="106" height="55" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="105" y="280" fill="#ff7b72" font-size="18" font-weight="700" text-anchor="middle">{suhu_ruang_bakar} °C</text>
      <text x="105" y="340" fill="#8890a1" font-size="9" text-anchor="middle">Sensor Suhu Ruang Bakar</text>

      <!-- Pipa Gas Panas ke Cerobong Filter -->
      <path d="M 170 270 L 195 270" stroke="#d19a38" stroke-width="3" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- Cerobong Peningkat & Filtrasi Partikulat Ganda -->
      <rect x="195" y="110" width="80" height="260" rx="6" fill="#1a1d29" stroke="#8890a1" stroke-width="1.5"/>
      <text x="235" y="138" fill="#e2e4e9" font-size="10" font-weight="700" text-anchor="middle">HEAT RISER</text>
      <text x="235" y="153" fill="#8890a1" font-size="9" text-anchor="middle">(Cerobong)</text>
      <line x1="195" y1="175" x2="275" y2="175" stroke="#333a4d" stroke-width="2"/>
      <text x="235" y="210" fill="#d19a38" font-size="9" font-weight="600" text-anchor="middle">Filter Kasar</text>
      <line x1="195" y1="245" x2="275" y2="245" stroke="#333a4d" stroke-width="2"/>
      <text x="235" y="290" fill="#3fb950" font-size="9" font-weight="600" text-anchor="middle">HEPA &amp; VOC</text>
      <text x="235" y="305" fill="#3fb950" font-size="8" text-anchor="middle">Gas Filter</text>

      <!-- Pipa Panas Bersih dari Filter ke Heat Exchanger -->
      <path d="M 275 270 L 320 270" stroke="#d19a38" stroke-width="3" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- Menara Koil Penukar Panas (Heat Exchanger Tower) -->
      <rect x="320" y="110" width="145" height="260" rx="6" fill="#182026" stroke="#3fb950" stroke-width="2"/>
      <text x="392" y="138" fill="#3fb950" font-size="11" font-weight="700" text-anchor="middle">HEAT EXCHANGER</text>
      <text x="392" y="155" fill="#8890a1" font-size="9" text-anchor="middle">Penukar Kalor Hibrida</text>
      <circle cx="392" cy="205" r="28" fill="#0f1015" stroke="#3fb950" stroke-width="2"/>
      <text x="392" y="210" fill="#3fb950" font-size="13" font-weight="700" text-anchor="middle">85%</text>
      
      <rect x="332" y="250" width="121" height="42" rx="4" fill="#0f1015" stroke="#252d3a"/>
      <text x="392" y="267" fill="#58a6ff" font-size="9" font-weight="600" text-anchor="middle">Inlet Udara Bersih</text>
      <text x="392" y="282" fill="#e2e4e9" font-size="9" text-anchor="middle">Dipanaskan Bersih</text>
      <text x="392" y="340" fill="#8890a1" font-size="9" text-anchor="middle">Efisiensi Termal Optimal</text>

      <!-- Saluran Udara Panas ke Rumah Pengering -->
      <path d="M 465 270 L 510 270" stroke="#d19a38" stroke-width="3.5" fill="none" marker-end="url(#arrow-amber)"/>

      <!-- Rumah Pengering Gabah 3 Bak Datar -->
      <rect x="510" y="110" width="160" height="380" rx="6" fill="#1a1c24" stroke="#d19a38" stroke-width="2"/>
      <text x="590" y="138" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">RUMAH PENGERING</text>
      <text x="590" y="155" fill="#8890a1" font-size="9" text-anchor="middle">Sistem 3 Bak Datar</text>
      
      <!-- 3 Bak Pengering dengan Margin Rapi -->
      <rect x="525" y="175" width="130" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="590" y="195" fill="#e2e4e9" font-size="11" font-weight="600" text-anchor="middle">Bak 1</text>
      <text x="590" y="213" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">KA: {ka_b1:.1f}%</text>

      <rect x="525" y="235" width="130" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="590" y="255" fill="#e2e4e9" font-size="11" font-weight="600" text-anchor="middle">Bak 2</text>
      <text x="590" y="273" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">KA: {ka_b2:.1f}%</text>

      <rect x="525" y="295" width="130" height="50" rx="4" fill="#0f1015" stroke="#333a4d"/>
      <text x="590" y="315" fill="#e2e4e9" font-size="11" font-weight="600" text-anchor="middle">Bak 3</text>
      <text x="590" y="333" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">KA: {ka_b3:.1f}%</text>

      <text x="590" y="380" fill="#3fb950" font-size="10" font-weight="600" text-anchor="middle">Blower Udara Aktif</text>
      <text x="590" y="405" fill="#8890a1" font-size="9" text-anchor="middle">Kapasitas Total:</text>
      <text x="590" y="420" fill="#e2e4e9" font-size="10" font-weight="600" text-anchor="middle">1 Ton / Siklus</text>

      <!-- 2. SISTEM PEMBANGKIT SURYA (PLTS DARAT 4.000 Wp) -->
      <rect x="710" y="20" width="330" height="520" rx="8" fill="#161822" stroke="#2b3246" stroke-width="1.5"/>
      <rect x="725" y="32" width="260" height="26" rx="4" fill="#202534"/>
      <text x="735" y="50" fill="#e2e4e9" font-size="12" font-weight="700" letter-spacing="0.5">2. SISTEM ENERGI SURYA (PLTS DARAT)</text>

      <!-- PV Array -->
      <rect x="730" y="80" width="290" height="110" rx="6" fill="#151d2a" stroke="#388bfd" stroke-width="2"/>
      <text x="875" y="118" fill="#58a6ff" font-size="12" font-weight="700" text-anchor="middle">ARRAY PANEL SURYA</text>
      <text x="875" y="145" fill="#e2e4e9" font-size="20" font-weight="700" text-anchor="middle">{suplai_plts_wp} Wp</text>
      <text x="875" y="168" fill="#8890a1" font-size="10" text-anchor="middle">Kapasitas Terpasang: 4.000 Wp Off-Grid</text>

      <path d="M 875 190 L 875 220" stroke="#58a6ff" stroke-width="2.5" fill="none" marker-end="url(#arrow-blue)"/>

      <!-- MPPT Charge Controller -->
      <rect x="755" y="220" width="240" height="60" rx="6" fill="#1d202d" stroke="#d19a38" stroke-width="1.5"/>
      <text x="875" y="244" fill="#d19a38" font-size="11" font-weight="700" text-anchor="middle">SOLAR CHARGE CONTROLLER</text>
      <text x="875" y="264" fill="#3fb950" font-size="10" font-weight="600" text-anchor="middle">Efisiensi Pelacakan MPPT: 98%</text>

      <path d="M 875 280 L 875 310" stroke="#3fb950" stroke-width="2.5" fill="none" marker-end="url(#arrow-green)"/>

      <!-- Baterai Storage -->
      <rect x="755" y="310" width="240" height="60" rx="6" fill="#1d202d" stroke="#3fb950" stroke-width="1.5"/>
      <text x="875" y="334" fill="#3fb950" font-size="11" font-weight="700" text-anchor="middle">BATERAI PENYIMPANAN</text>
      <text x="875" y="355" fill="#e2e4e9" font-size="13" font-weight="700" text-anchor="middle">{status_baterai:.1f}% Kapasitas Tersedia</text>

      <!-- Beban Kelistrikan Terpasang -->
      <rect x="730" y="395" width="290" height="95" rx="6" fill="#0f1015" stroke="#2b3246"/>
      <text x="745" y="420" fill="#8890a1" font-size="10" font-weight="600">PENYALURAN DAYA OPERASIONAL:</text>
      <text x="745" y="443" fill="#e2e4e9" font-size="10.5">• Blower Sirkulasi Udara Termal (2x 500W)</text>
      <text x="745" y="465" fill="#e2e4e9" font-size="10.5">• Mikrokontroler IoT, Sensor &amp; Gateway Data</text>
    </svg>
    """
    st.components.v1.html(svg_hmi_industrial, height=580)

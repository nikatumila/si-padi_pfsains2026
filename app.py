"""
SI-PADI-Panel Monitoring & Kendali Pengering Gabah Hibrida Surya-Biomassa (demo 4 menit)

Jalankan:   streamlit run app.py
Kebutuhan:  streamlit >= 1.50 (st.fragment, parameter width), pandas, altair

4 menit demo = 24 jam proses (10 detik = 1 jam). Model dikalibrasi ke hasil uji lapangan:
KA 27,72 % bb -> 14 % bb dalam 18-24 jam untuk ±1 ton gabah per batch.
"""
import time
from datetime import datetime, timedelta, timezone

import altair as alt
import pandas as pd
import streamlit as st
import math
import random

# ==============================================================================
# 1. PARAMETER SIMULASI
#    Angka bertanda [DESAIN] adalah data desain & hasil uji SI-PADI.
#    Angka bertanda [ASUMSI] adalah asumsi desain untuk demo; tampilkan
#    apa adanya bila juri bertanya.
# ==============================================================================
DEMO_DETIK = 240                 # 4 menit presentasi
SIKLUS_JAM = 24.0                # [DESAIN] siklus pengeringan 18-24 jam
JAM_PER_DETIK = SIKLUS_JAM / DEMO_DETIK   # 1 detik demo = 0,1 jam = 6 menit proses; 10 detik = 1 jam
JAM_MULAI = 8.0                  # [ASUMSI] batch dimuat pukul 08:00
DT_JAM = 0.02                    # langkah integrasi model (±1,2 menit proses)
REKAM_TIAP_JAM = 0.1             # resolusi log/grafik

MASSA_AWAL_KG = 1000.0           # [DESAIN] ±1 ton gabah segar per batch
KA_AWAL_WB = 27.72               # [DESAIN] kadar air awal basis basah
KA_TARGET_WB = 14.0              # [DESAIN] target akhir

ZONA = ["bawah", "tengah", "atas"]      # urutan aliran udara: masuk dari bawah
NAMA_ZONA = {"atas": "Rak Atas", "tengah": "Rak Tengah", "bawah": "Rak Bawah"}
NOMOR_ZONA = {"atas": 1, "tengah": 2, "bawah": 3}
KA_AWAL_ZONA = {"bawah": 27.6, "tengah": 27.7, "atas": 27.85}   # variasi muat kecil
# Konstanta laju (1/jam, pada 45 °C). Rak bawah menerima udara paling panas & kering.
K0_ZONA = {"bawah": 0.081, "tengah": 0.076, "atas": 0.077}
PENURUNAN_SUHU = {"bawah": 0.6, "tengah": 2.2, "atas": 3.8}      # °C, pendinginan evaporatif
TAMBAHAN_RH = {"bawah": 4.0, "tengah": 10.0, "atas": 17.0}      # % RH, uap air terbawa ke atas
EA_R = 3600.0                    # [ASUMSI] energi aktivasi/R (K) untuk gabah

# Energi listrik
PV_WP = 4000.0                   # [DESAIN] PLTS ±4.000 Wp
PERFORMANCE_RATIO = 0.80         # [ASUMSI]
BATERAI_KWH = 10.0               # [ASUMSI] LiFePO4 48 V 200 Ah
SOC_AWAL = 85.0
SOC_HEMAT = 30.0                 # di bawah ini blower 70 %
SOC_GRID = 15.0                  # di bawah ini ambil cadangan jaringan (on-grid hybrid)
P_BLOWER_MAKS_W = 2 * 250.0      # [ASUMSI] 2 unit blower DC (jumlah unit sesuai RAB)
P_IOT_W = 25.0
P_LAMPU_W = 40.0
P_FAN_TUNGKU_W = 60.0

# Termal
Q_TUNGKU_MAKS_KW = 30.0          # [ASUMSI] kalor maksimum ke udara pengering
LHV_JERAMI = 14.0                # MJ/kg batang padi kering [ASUMSI literatur]
EFISIENSI_TUNGKU_HE = 0.55       # [ASUMSI]
ALIRAN_UDARA_KGS = 1.2           # kg/s pada blower 100 %
T_MAKS_GABAH = 50.0              # batas alarm suhu rak

# Ambang alarm emisi internal (sesuaikan dengan baku mutu yang berlaku)
AMBANG_CO = 500.0                # mg/Nm3
AMBANG_PM = 50.0                 # mg/Nm3
AMBANG_DP_FILTER = 400.0         # Pa

CUACA = {
    "cerah": {"label": "Cerah", "awan": 1.00, "hujan": False},
    "berawan": {"label": "Berawan", "awan": 0.45, "hujan": False},
    "hujan": {"label": "Hujan", "awan": 0.12, "hujan": True},
}


# ==============================================================================
# 2. FUNGSI BANTU
# ==============================================================================
def wb_ke_db(wb):
    return wb / (100.0 - wb) * 100.0


def db_ke_wb(db):
    return db / (100.0 + db) * 100.0


def psat(t):
    return 6.112 * math.exp(17.62 * t / (243.12 + t))


def ka_setimbang_db(rh_persen, t):
    """Kadar air setimbang gabah (Henderson termodifikasi, konstanta gabah ASAE D245)."""
    rh = min(max(rh_persen / 100.0, 0.05), 0.97)
    a, b, c = 1.9187e-5, 51.161, 2.4451
    return (math.log(1 - rh) / (-a * (t + b))) ** (1.0 / c)


def fraksi_matahari(jam_lokal):
    h = jam_lokal % 24
    if 6.0 < h < 18.0:
        return math.sin(math.pi * (h - 6.0) / 12.0)
    return 0.0


def cuaca_skenario(jam_lokal):
    """Skenario demo: pagi cerah, siang berawan, sore hujan, malam, pagi cerah."""
    h = jam_lokal % 24
    if 12.0 <= h < 14.0:
        return "berawan"
    if 14.0 <= h < 16.0:
        return "hujan"
    if 16.0 <= h < 17.5:
        return "berawan"
    return "cerah"


def format_jam(jam_lokal):
    menit = int(round(jam_lokal * 60)) % (24 * 60)
    return f"{menit // 60:02d}:{menit % 60:02d}"


# ==============================================================================
# 3. STATE AWAL
# ==============================================================================
def buat_state_awal(seed=7):
    s = _state_kosong(seed)
    rekam(s, 45)
    return s


def _state_kosong(seed):
    massa_rak = MASSA_AWAL_KG / 3
    zona = {}
    for z in ZONA:
        ka = KA_AWAL_ZONA[z]
        zona[z] = {
            "ka_db": wb_ke_db(ka),
            "bahan_kering": massa_rak * (1 - ka / 100.0),
            "suhu": 30.0,
            "rh": 70.0,
            "laju": 0.0,              # %wb per jam
            "status": "Proses",
            "jam_selesai": None,
        }
    return {
        "jam": 0.0,
        "rng": random.Random(seed),
        "zona": zona,
        "t_masuk": 30.0,
        "t_tungku": 60.0,
        "firing": 0.0,
        "integral_pi": 0.0,
        "blower": 1.0,
        "pemanas_on": True,
        "soc": SOC_AWAL,
        "kwh_pv": 0.0,
        "kwh_beban": 0.0,
        "kwh_grid": 0.0,
        "kg_biomassa": 0.0,
        "mj_panas": 0.0,
        "mj_surya": 0.0,
        "sumber_listrik": "PLTS",
        "mode_energi": "Normal",
        "cuaca": "cerah",
        "t_amb": 28.0,
        "rh_amb": 70.0,
        "iradiasi": 0.0,
        "p_pv": 0.0,
        "p_beban": 0.0,
        "co": 0.0,
        "pm": 0.0,
        "dp_filter": 180.0,
        "eff_he": 0.0,
        "t_gas_he": 60.0,
        "t_cerobong": 40.0,
        "selesai": False,
        "jam_selesai_batch": None,
        "fase_akhir": None,       # None | "pendinginan" | "berhenti"
        "log": [{"Jam proses": 0.0, "Jam lokal": format_jam(JAM_MULAI), "Tingkat": "Info",
                 "Kejadian": "Batch 1.000 kg dimuat, KA awal " + f"{KA_AWAL_WB:.2f}".replace(".", ",") + " %. Tungku mulai dipanaskan"}],
        "flag": {},
        "riwayat": [],
        "jam_rekam_berikut": REKAM_TIAP_JAM,
    }


def catat(s, tingkat, pesan):
    s["log"].append({
        "Jam proses": round(s["jam"], 2),
        "Jam lokal": format_jam(JAM_MULAI + s["jam"]),
        "Tingkat": tingkat,
        "Kejadian": pesan,
    })


def transisi(s, kunci, kondisi, tingkat, pesan_on, pesan_off=None):
    lama = s["flag"].get(kunci, False)
    if kondisi and not lama:
        catat(s, tingkat, pesan_on)
    elif not kondisi and lama and pesan_off:
        catat(s, "Info", pesan_off)
    s["flag"][kunci] = kondisi


# ==============================================================================
# 4. SATU LANGKAH MODEL
# ==============================================================================
def langkah(s, dt, kendali):
    """kendali: dict berisi mode, setpoint, target_ka, blower_manual,
    pemanas_manual, pilihan_cuaca."""
    rng = s["rng"]
    jam_lokal = JAM_MULAI + s["jam"]
    target_db = wb_ke_db(kendali["target_ka"])

    # ---- Cuaca & lingkungan -------------------------------------------------
    cuaca = cuaca_skenario(jam_lokal) if kendali["pilihan_cuaca"] == "skenario" else kendali["pilihan_cuaca"]
    if cuaca != s["cuaca"] and s["jam"] > 0:
        pesan = {
            "cerah": "Cuaca cerah: daya PLTS naik, pemakaian biomassa turun",
            "berawan": "Cuaca berawan: daya PLTS turun, tungku menambah panas",
            "hujan": "Hujan: daya PLTS minim, tungku biomassa menjaga suhu",
        }[cuaca]
        catat(s, "Info", pesan)
    s["cuaca"] = cuaca
    c = CUACA[cuaca]
    fm = fraksi_matahari(jam_lokal)
    s["iradiasi"] = 1000.0 * fm * c["awan"]
    s["t_amb"] = 24.0 + 8.0 * fm * (0.5 + 0.5 * c["awan"]) - (2.0 if c["hujan"] else 0.0)
    s["rh_amb"] = min(97.0, max(45.0, 88.0 - 30.0 * fm * (0.5 + 0.5 * c["awan"]) + (7.0 if c["hujan"] else 0.0)))

    # ---- Aktuator (otomatis vs manual) --------------------------------------
    otomatis = kendali["mode"] == "otomatis"
    if s["fase_akhir"] == "berhenti":
        blower, pemanas_on = 0.0, False
    elif s["fase_akhir"] == "pendinginan":
        blower, pemanas_on = 1.0, False
    elif otomatis:
        if s["soc"] < SOC_HEMAT and s["sumber_listrik"] != "Grid":
            blower = 0.7
        else:
            blower = 1.0
        pemanas_on = True
    else:
        blower = 1.0 if kendali["blower_manual"] else 0.0
        pemanas_on = kendali["pemanas_manual"]

    transisi(s, "manual", not otomatis, "Info",
             "Mode manual: operator mengendalikan blower dan tungku",
             "Mode otomatis aktif kembali")
    transisi(s, "pemanas_off", (not pemanas_on) and blower > 0 and not s["fase_akhir"], "Peringatan",
             "Tungku dimatikan: suhu turun, pengeringan melambat",
             "Tungku menyala kembali")

    # Interlock keselamatan: tanpa aliran udara pemanas tidak boleh menyala
    interlock = blower == 0.0 and pemanas_on
    transisi(s, "interlock", interlock, "Kritis",
             "Blower mati: tungku dikunci otomatis agar tidak panas berlebih",
             "Blower menyala kembali: kunci tungku dilepas")
    if blower == 0.0:
        pemanas_on = False
    s["blower"], s["pemanas_on"] = blower, pemanas_on

    # ---- Kendali suhu (PI) --------------------------------------------------
    aliran = ALIRAN_UDARA_KGS * blower
    dt_surya = 12.0 * s["iradiasi"] / 1000.0          # efek rumah kaca polikarbonat
    if pemanas_on:
        if otomatis:
            galat = kendali["setpoint"] - s["t_masuk"]
            s["integral_pi"] = min(max(s["integral_pi"] + galat * dt, -2.0), 12.0)
            firing = 0.08 * galat + 0.12 * s["integral_pi"]
        else:
            firing = 0.6
        firing = min(max(firing, 0.0), 1.0)
    else:
        firing = 0.0
        s["integral_pi"] = 0.0
    s["firing"] += (firing - s["firing"]) * min(1.0, dt / 0.05)

    if aliran > 0:
        dt_pemanas = s["firing"] * Q_TUNGKU_MAKS_KW / (aliran * 1.005)
        t_potensial = s["t_amb"] + dt_surya + dt_pemanas
        tau = 0.15
    else:
        t_potensial = s["t_amb"] + dt_surya * 1.6
        tau = 0.6
    s["t_masuk"] += (t_potensial - s["t_masuk"]) * dt / tau + rng.uniform(-0.05, 0.05)
    s["mj_surya"] += aliran * 1.005 * dt_surya * 3.6 * dt      # panas surya lewat atap polikarbonat

    # ---- Tungku, penukar panas, emisi --------------------------------------
    t_tungku_target = (150.0 + 380.0 * s["firing"]) if s["firing"] > 0.02 else s["t_amb"] + 20
    s["t_tungku"] += (t_tungku_target - s["t_tungku"]) * dt / 0.3
    q_kw = s["firing"] * Q_TUNGKU_MAKS_KW
    s["kg_biomassa"] += q_kw * 3.6 / (LHV_JERAMI * EFISIENSI_TUNGKU_HE) * dt
    s["mj_panas"] += q_kw * 3.6 * dt
    s["t_gas_he"] = max(s["t_amb"], s["t_tungku"] - 60.0)
    if s["firing"] > 0.02:
        # efektivitas HE turun sedikit saat laju gas buang tinggi
        s["eff_he"] = 0.83 - 0.10 * s["firing"] + rng.uniform(-0.005, 0.005)
        s["t_cerobong"] = s["t_gas_he"] - s["eff_he"] * (s["t_gas_he"] - s["t_amb"])
        s["co"] = 120 + 250 * max(0.0, (380 - s["t_tungku"]) / 200) + rng.uniform(-15, 15)
        pm_mentah = 400 + 300 * s["firing"]
        s["pm"] = pm_mentah * 0.30 * (0.05 + 0.00005 * s["dp_filter"]) + rng.uniform(-0.5, 0.5)
    else:
        s["eff_he"] = 0.0
        s["t_cerobong"] += (s["t_amb"] - s["t_cerobong"]) * min(1.0, dt / 0.3)
        s["co"] = max(0.0, s["co"] - 200 * dt)
        s["pm"] = max(0.0, s["pm"] - 20 * dt)
    s["dp_filter"] = 180.0 + 0.9 * s["kg_biomassa"]

    # ---- Pengeringan per rak ------------------------------------------------
    rh_masuk = min(97.0, s["rh_amb"] * psat(s["t_amb"]) / psat(s["t_masuk"]))
    semua_selesai = True
    for z in ZONA:
        d = s["zona"][z]
        mr = max(0.0, (d["ka_db"] - target_db) / (wb_ke_db(KA_AWAL_WB) - target_db))
        if aliran > 0:
            d["suhu"] = s["t_masuk"] - PENURUNAN_SUHU[z] * (0.5 + 0.5 * mr) + rng.uniform(-0.15, 0.15)
            rh_target = rh_masuk + TAMBAHAN_RH[z] * (0.4 + 0.6 * mr) * (1.0 / blower)
        else:
            d["suhu"] = s["t_masuk"] - 0.3 + rng.uniform(-0.1, 0.1)
            rh_target = 85.0
        d["rh"] += (min(96.0, rh_target) - d["rh"]) * min(1.0, dt / 0.2)

        if d["status"] == "Selesai":
            if not s["selesai"] and d["ka_db"] > target_db + 1e-6:
                # target diturunkan saat batch masih berjalan: rak dikeringkan lagi
                d["status"], d["jam_selesai"] = "Proses", None
                catat(s, "Info", f"Target diturunkan: {NAMA_ZONA[z]} dikeringkan lagi")
            else:
                d["laju"] = 0.0
                continue
        if d["ka_db"] <= target_db:
            # target dinaikkan melewati KA rak saat ini: selesai tanpa mengubah KA
            d["status"], d["jam_selesai"], d["laju"] = "Selesai", s["jam"], 0.0
            catat(s, "Sukses", f"{NAMA_ZONA[z]} sudah di bawah target baru "
                               f"{kendali['target_ka']:.1f} %, siap dibongkar".replace(".", ","))
            continue
        semua_selesai = False
        me = ka_setimbang_db(d["rh"], d["suhu"])
        faktor_aliran = math.sqrt(blower) if aliran > 0 else 0.08
        k = K0_ZONA[z] * math.exp(-EA_R * (1 / (d["suhu"] + 273.15) - 1 / 318.15)) * faktor_aliran
        wb_lama = db_ke_wb(d["ka_db"])
        if d["ka_db"] > me:
            d["ka_db"] = me + (d["ka_db"] - me) * math.exp(-k * dt)
        if d["ka_db"] <= target_db:
            d["ka_db"] = target_db
            d["status"] = "Selesai"
            d["jam_selesai"] = s["jam"] + dt
            catat(s, "Sukses", f"{NAMA_ZONA[z]} mencapai {kendali['target_ka']:.1f} %, siap dibongkar".replace(".", ","))
        d["laju"] = (wb_lama - db_ke_wb(d["ka_db"])) / dt

    # ---- Akhir batch --------------------------------------------------------
    semua_selesai = all(s["zona"][z]["status"] == "Selesai" for z in ZONA)
    if semua_selesai and not s["selesai"]:
        s["selesai"] = True
        s["jam_selesai_batch"] = s["jam"] + dt
        s["fase_akhir"] = "pendinginan"
        catat(s, "Sukses", "Semua rak mencapai target: tungku mati, blower mendinginkan 30 menit")
    if s["fase_akhir"] == "pendinginan" and s["jam"] - s["jam_selesai_batch"] >= 0.5:
        s["fase_akhir"] = "berhenti"
        catat(s, "Info", "Pendinginan selesai: batch siap dibongkar")

    # ---- Neraca listrik -----------------------------------------------------
    s["p_pv"] = PV_WP * s["iradiasi"] / 1000.0 * PERFORMANCE_RATIO
    s["p_beban"] = (P_BLOWER_MAKS_W * blower ** 3 + P_IOT_W
                    + (P_LAMPU_W if fm == 0 else 0.0) + P_FAN_TUNGKU_W * (1.0 if s["firing"] > 0.02 else 0.0))
    net_kw = (s["p_pv"] - s["p_beban"]) / 1000.0
    s["kwh_pv"] += s["p_pv"] / 1000.0 * dt
    s["kwh_beban"] += s["p_beban"] / 1000.0 * dt
    if s["sumber_listrik"] == "Grid" and s["soc"] < SOC_GRID + 10:
        s["kwh_grid"] += max(0.0, -net_kw) * dt
        net_kw = max(0.0, net_kw)
    efis = 0.95 if net_kw > 0 else 1 / 0.95
    s["soc"] = min(100.0, max(0.0, s["soc"] + net_kw * dt * efis / BATERAI_KWH * 100.0))

    if s["soc"] < SOC_GRID and s["sumber_listrik"] != "Grid":
        s["sumber_listrik"] = "Grid"
        catat(s, "Peringatan", "Baterai di bawah 15 %: listrik pindah ke jaringan PLN")
    elif s["sumber_listrik"] == "Grid" and s["soc"] >= SOC_GRID + 10:
        s["sumber_listrik"] = "PLTS"
        catat(s, "Info", "Baterai pulih: listrik kembali dari PLTS")
    elif s["sumber_listrik"] != "Grid":
        s["sumber_listrik"] = ("PLTS" if s["p_pv"] >= s["p_beban"] else
                               "Baterai" if s["p_pv"] < 20 else "PLTS + Baterai")

    hemat = otomatis and blower == 0.7
    if s["fase_akhir"]:
        s["flag"]["hemat"] = hemat = False
    transisi(s, "hemat", hemat, "Peringatan",
             "Baterai di bawah 30 %: hemat energi, blower 70 %",
             "Energi cukup: blower kembali 100 %")
    s["mode_energi"] = "Hemat" if hemat else "Normal"

    transisi(s, "malam", fm == 0.0, "Info",
             "Matahari terbenam: listrik dari baterai",
             "Matahari terbit: PLTS mengisi baterai")

    # ---- Alarm proses -------------------------------------------------------
    maks_suhu = max(s["zona"][z]["suhu"] for z in ZONA)
    transisi(s, "panas", maks_suhu > T_MAKS_GABAH, "Kritis",
             f"Suhu rak di atas {T_MAKS_GABAH:.0f} °C: risiko gabah retak",
             "Suhu rak kembali normal")
    ka_aktif = [db_ke_wb(s["zona"][z]["ka_db"]) for z in ZONA]
    transisi(s, "selisih", max(ka_aktif) - min(ka_aktif) > 5.0, "Peringatan",
             "Selisih KA antar rak di atas 5 %: pertimbangkan rotasi rak",
             "KA antar rak kembali seragam")
    transisi(s, "co", s["co"] > AMBANG_CO and s["jam"] > 0.5, "Peringatan",
             "CO gas buang di atas ambang: periksa pasokan udara tungku",
             "CO gas buang kembali normal")
    transisi(s, "pm", s["pm"] > AMBANG_PM, "Peringatan",
             "Partikulat di atas ambang: periksa filter", "Partikulat kembali normal")
    transisi(s, "filter", s["dp_filter"] > AMBANG_DP_FILTER, "Peringatan",
             "Tekanan filter tinggi: jadwalkan pembersihan")

    s["jam"] += dt

    # ---- Rekam riwayat ------------------------------------------------------
    if s["jam"] >= s["jam_rekam_berikut"] - 1e-9:
        s["jam_rekam_berikut"] += REKAM_TIAP_JAM
        rekam(s, kendali["setpoint"])


def rekam(s, setpoint):
    baris = {
        "jam": round(s["jam"], 2),
        "jam_lokal": format_jam(JAM_MULAI + s["jam"]),
        "cuaca": CUACA[s["cuaca"]]["label"],
        "t_amb": round(s["t_amb"], 1),
        "rh_amb": round(s["rh_amb"], 1),
        "t_masuk": round(s["t_masuk"], 1),
        "setpoint": setpoint,
        "t_tungku": round(s["t_tungku"], 0),
        "firing": round(s["firing"] * 100, 1),
        "biomassa_kg": round(s["kg_biomassa"], 1),
        "iradiasi": round(s["iradiasi"], 0),
        "p_pv": round(s["p_pv"], 0),
        "p_beban": round(s["p_beban"], 0),
        "soc": round(s["soc"], 1),
        "co": round(s["co"], 0),
        "pm": round(s["pm"], 1),
        "dp_filter": round(s["dp_filter"], 0),
        "eff_he": round(s["eff_he"] * 100, 1),
        "blower": round(s["blower"] * 100),
    }
    for z in ZONA:
        d = s["zona"][z]
        baris[f"ka_{z}"] = round(db_ke_wb(d["ka_db"]), 2)
        baris[f"suhu_{z}"] = round(d["suhu"], 1)
        baris[f"rh_{z}"] = round(d["rh"], 1)
    s["riwayat"].append(baris)


def maju_ke(s, jam_tujuan, kendali):
    jam_tujuan = min(jam_tujuan, SIKLUS_JAM)
    while s["jam"] + 1e-9 < jam_tujuan:
        langkah(s, min(DT_JAM, jam_tujuan - s["jam"]), kendali)
    if s["jam"] >= SIKLUS_JAM - 1e-6 and not s["selesai"]:
        transisi(s, "timeout", True, "Kritis",
                 "24 jam tercapai, KA belum semua di target")


# ==============================================================================
# 5. TURUNAN UNTUK TAMPILAN
# ==============================================================================
def prediksi_selesai(s, kendali, dt=0.1, horizon=30.0):
    """Jalankan salinan model ke depan (digital twin) dengan kendali & skenario cuaca saat ini.
    Mengembalikan jam proses saat batch diperkirakan selesai, atau None bila tidak tercapai."""
    if s["selesai"]:
        return s["jam_selesai_batch"]
    c = dict(s)
    c["zona"] = {z: dict(v) for z, v in s["zona"].items()}
    c["flag"] = dict(s["flag"])
    c["log"], c["riwayat"] = [], []
    c["rng"] = random.Random(1)
    c["jam_rekam_berikut"] = float("inf")
    batas = s["jam"] + horizon
    while not c["selesai"] and c["jam"] < batas:
        langkah(c, dt, kendali)
    return c["jam_selesai_batch"] if c["selesai"] else None


def ringkasan(s, target_ka):
    massa = 0.0
    for z in ZONA:
        d = s["zona"][z]
        massa += d["bahan_kering"] * (1 + d["ka_db"] / 100.0)
    ka_rata = sum(db_ke_wb(s["zona"][z]["ka_db"]) * 1 for z in ZONA) / 3
    target_db = wb_ke_db(target_ka)
    sisa = 0.0
    for z in ZONA:
        d = s["zona"][z]
        if d["status"] == "Selesai":
            continue
        me = ka_setimbang_db(d["rh"], d["suhu"])
        k = K0_ZONA[z] * math.exp(-EA_R * (1 / (d["suhu"] + 273.15) - 1 / 318.15)) * math.sqrt(max(s["blower"], 0.01))
        if d["ka_db"] <= me + 0.05 or target_db <= me + 0.05 or s["blower"] == 0:
            sisa = float("inf")
            break
        sisa = max(sisa, math.log((d["ka_db"] - me) / (target_db - me)) / k)
    air_menguap = MASSA_AWAL_KG - massa
    # Ekuivalen emisi yang dihindari (estimasi kasar untuk narasi)
    mj_listrik_pv = max(0.0, s["kwh_beban"] - s["kwh_grid"]) * 3.6
    mj_grid = s["kwh_grid"] * 3.6
    total = s["mj_panas"] + s["mj_surya"] + mj_listrik_pv + mj_grid
    lpg_kg = s["mj_panas"] / (46.0 * 0.85)
    co2_dihindari = lpg_kg * 2.98 + s["kwh_pv"] * 0.87
    return {
        "massa": massa,
        "ka_rata": ka_rata,
        "sisa_jam": sisa,
        "air_menguap": air_menguap,
        "co2_dihindari": co2_dihindari,
        "porsi_terbarukan": 100.0 if total <= 0 else (total - mj_grid) / total * 100,
        "porsi_listrik_pv": 100.0 if s["kwh_beban"] <= 0 else (1 - s["kwh_grid"] / s["kwh_beban"]) * 100,
        "porsi_surya": 0.0 if total <= 0 else (s["mj_surya"] + mj_listrik_pv) / total * 100,
        "selesai": sum(1 for z in ZONA if s["zona"][z]["status"] == "Selesai"),
    }


# ==============================================================================
# ==============================================================================
#                                  TAMPILAN
# ==============================================================================
# ==============================================================================
WIB = timezone(timedelta(hours=7))
WARNA_ZONA = {"bawah": "#ff7b72", "tengah": "#d19a38", "atas": "#58a6ff"}
URUTAN_TAMPIL = ["atas", "tengah", "bawah"]     # sesuai posisi fisik rak

st.set_page_config(
    page_title="SI-PADI - Panel Monitoring Pengering Gabah",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background-color: #0f1015; color: #e2e4e9; }
.block-container { padding-top: 3rem; }
.topbar { display:flex; justify-content:space-between; align-items:flex-start; gap:18px; flex-wrap:wrap;
  background:linear-gradient(180deg,#181b24 0%,#13151c 100%); border:1px solid #282d3c; border-radius:10px;
  padding:16px 22px; margin-bottom:14px; }
.topbar h1 { font-size:22px; font-weight:700; color:#f1f3f7; margin:0; padding:0; letter-spacing:-0.2px; }
.topbar p { font-size:13px; color:#9299a8; margin:4px 0 0 0; }
.chips { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
.chip { background:#1a1e29; border:1px solid #333a4d; border-radius:6px; padding:5px 11px; font-size:12.5px; color:#c9ccd4; }
.chip b { color:#f1f3f7; }
.chip.jam { color:#d19a38; font-weight:700; font-variant-numeric:tabular-nums; }
.demo-bar { height:6px; background:#1f2431; border-radius:4px; overflow:hidden; margin:2px 0 16px 0; }
.demo-bar i { display:block; height:100%; background:linear-gradient(90deg,#d19a38,#3fb950); }
.kpi-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; margin-bottom:16px; }
@media (max-width: 1100px) { .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.kpi { background:#141720; border:1px solid #232838; border-radius:8px; padding:13px 16px; }
.kpi-j { font-size:12.5px; color:#8890a1; margin-bottom:6px; }
.kpi-n { font-size:27px; font-weight:700; line-height:1.1; font-variant-numeric:tabular-nums; }
.kpi-s { font-size:12px; color:#697184; margin-top:5px; }
.kabinet { display:flex; gap:12px; background:#12141c; border:1px solid #232838; border-radius:10px; padding:12px; margin-bottom:10px; }
.aliran { width:34px; border-radius:6px; background:linear-gradient(0deg,rgba(255,123,114,.55) 0%,rgba(209,154,56,.35) 50%,rgba(88,166,255,.25) 100%);
  display:flex; align-items:center; justify-content:center; }
.aliran span { writing-mode:vertical-rl; transform:rotate(180deg); font-size:11px; color:#f1f3f7; letter-spacing:.3px; white-space:nowrap; }
.rak-list { flex:1; display:flex; flex-direction:column; gap:8px; }
.ventilasi { font-size:11.5px; color:#8890a1; padding:0 4px 2px 4px; }
.rak { display:grid; grid-template-columns:1.35fr .75fr .6fr .85fr 1.6fr .7fr; gap:10px; align-items:center;
  background:#141720; border:1px solid #232838; border-left:4px solid var(--c); border-radius:8px; padding:10px 14px; }
@media (max-width: 900px) { .rak { grid-template-columns:1fr 1fr 1fr; } }
.rak-nama { font-size:15px; font-weight:700; color:#f1f3f7; }
.rak-nama small { display:block; font-size:11.5px; color:#697184; font-weight:400; margin-top:2px; }
.ukur label { display:block; font-size:11.5px; color:#8890a1; }
.ukur b { font-size:16px; color:#f1f3f7; font-variant-numeric:tabular-nums; }
.ka b { font-size:22px; font-variant-numeric:tabular-nums; }
.bar { height:6px; background:#1f2431; border-radius:4px; overflow:hidden; margin-top:5px; }
.bar i { display:block; height:100%; }
.ka small { font-size:11px; color:#697184; }
.pill { justify-self:end; border-radius:4px; padding:3px 9px; font-size:11.5px; font-weight:600; white-space:nowrap; }
.pill.proses { background:#2b2111; color:#e5a43b; border:1px solid #543f1e; }
.pill.selesai { background:#12281a; color:#3fb950; border:1px solid #238636; }
.pill.henti { background:#2a1414; color:#ff7b72; border:1px solid #6e2b2b; }
.panel-j { font-size:14px; font-weight:700; color:#d19a38; margin-bottom:4px; }
.akt { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:6px 0 4px 0; }
.akt div { background:#0f1015; border:1px solid #232838; border-radius:6px; padding:8px 10px; font-size:12px; color:#8890a1; }
.akt b { display:block; font-size:15px; color:#f1f3f7; margin-top:2px; }
.alarm { border-radius:6px; padding:8px 10px; font-size:12.5px; margin-bottom:6px; border:1px solid; }
.alarm.Kritis { background:#2a1414; border-color:#6e2b2b; color:#ffb3ad; }
.alarm.Peringatan { background:#2b2111; border-color:#543f1e; color:#f0c476; }
.alarm.ok { background:#12281a; border-color:#238636; color:#8fe0a0; }
.logi { font-size:12px; color:#9299a8; padding:5px 0; border-bottom:1px solid #1f2431; }
.logi b { color:#c9ccd4; font-variant-numeric:tabular-nums; }
.catatan { font-size:12.5px; color:#8890a1; line-height:1.55; }
/* Hilangkan kedip saat data diperbarui tiap detik */
[data-testid="stStatusWidget"] { visibility:hidden !important; }
[data-stale="true"], [data-stale="true"] * { opacity:1 !important; transition:none !important; filter:none !important; }
.sek-j { font-size:19px; font-weight:700; color:#f1f3f7; margin:26px 0 4px 0; letter-spacing:-0.2px; }
.sek-j.pertama { margin-top:6px; }
.sek-s { font-size:13px; color:#8890a1; margin:0 0 10px 0; }
.spek-wrap { border:1px solid #232838; border-radius:10px; overflow:hidden; margin-bottom:6px; }
.spek { width:100%; border-collapse:collapse; table-layout:fixed; }
.spek th { background:#181b24; color:#8890a1; font-size:13px; font-weight:600; text-align:left; padding:10px 18px; }
.spek td { padding:10px 18px; border-top:1px solid #1f2431; font-size:14.5px; line-height:1.55; color:#e2e4e9;
  vertical-align:top; overflow-wrap:break-word; }
.spek td.kiri { color:#9299a8; }
.spek tr:hover td { background:#141720; }
.spek th, .spek td { border-left:none !important; border-right:none !important; border-bottom:none !important; }
.spek.ringkas td { padding:6px 18px; font-size:13.5px; }
.spek td.num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
.spek tr.grup td { background:#161a24; color:#d19a38; font-weight:700; font-size:13.5px; }
.spek tr.total td { background:#181b24; font-weight:700; color:#f1f3f7; }
.rab-bar { display:flex; height:14px; border-radius:7px; overflow:hidden; margin:6px 0 12px 0; }
.rab-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-bottom:10px; }
@media (max-width:900px) { .rab-grid { grid-template-columns:1fr; } }
.rab-kartu { background:#141720; border:1px solid #232838; border-left:4px solid var(--c); border-radius:8px; padding:12px 16px; }
.rab-kartu .n { font-size:13px; color:#9299a8; }
.rab-kartu .v { font-size:22px; font-weight:700; color:#f1f3f7; margin-top:2px; font-variant-numeric:tabular-nums; }
.rab-kartu .p { font-size:12.5px; color:#697184; margin-top:2px; }
.hmi svg { width:100%; height:auto; display:block; }
.hmi .pipa { fill:none; stroke:#232838; stroke-width:8; stroke-linecap:round; stroke-linejoin:round; }
.hmi .alir { fill:none; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; stroke-dasharray:8 7;
  animation:alir 1s linear infinite; }
@keyframes alir { to { stroke-dashoffset:-15; } }
.hmi .cepat { animation-duration:.5s; }
.hmi .sedang { animation-duration:.95s; }
.hmi .lambat { animation-duration:1.7s; }
.hmi .alir.mati { stroke:#3a4052; animation:none; stroke-dasharray:none; }
.hmi .kipas { transform-box:fill-box; transform-origin:center; animation:putar .5s linear infinite; }
.hmi .kipas.diam { animation:none; }
@keyframes putar { to { transform:rotate(360deg); } }
.hmi .api { transform-box:fill-box; transform-origin:50% 100%; animation:api .45s ease-in-out infinite alternate; }
@keyframes api { from { transform:scaleY(.78); opacity:.7; } to { transform:scaleY(1.08); opacity:1; } }
.hmi.jeda .alir, .hmi.jeda .kipas, .hmi.jeda .api { animation-play-state:paused; }
@media (prefers-reduced-motion: reduce) { .hmi .alir, .hmi .kipas, .hmi .api { animation:none; } }
</style>
""", unsafe_allow_html=True)


def html(s):
    """Streamlit menganggap baris berindentasi sebagai blok kode - rapatkan dulu."""
    st.markdown(" ".join(baris.strip() for baris in s.splitlines() if baris.strip()), unsafe_allow_html=True)


def f1(x, d=1):
    return f"{x:,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")


# ==============================================================================
# STATE SESI
# ==============================================================================
def reset_demo():
    st.session_state.sim = buat_state_awal()
    st.session_state.berjalan = False
    st.session_state.detik_akumulasi = 0.0
    st.session_state.t_mulai = None


if "sim" not in st.session_state:
    reset_demo()
for kunci, awal in {"k_mode": "Otomatis (PID)", "k_sp": 45, "k_target": 14.0,
                    "k_blower": True, "k_pemanas": True, "k_cuaca": "Skenario demo (otomatis)"}.items():
    st.session_state.setdefault(kunci, awal)

PILIHAN_CUACA = {
    "Skenario demo (otomatis)": "skenario",
    "Cerah sepanjang hari": "cerah",
    "Berawan sepanjang hari": "berawan",
    "Hujan sepanjang hari": "hujan",
}


def detik_demo():
    d = st.session_state.detik_akumulasi
    if st.session_state.berjalan and st.session_state.t_mulai is not None:
        d += time.time() - st.session_state.t_mulai
    return min(float(DEMO_DETIK), d)


def kendali():
    ss = st.session_state
    return {
        "mode": "otomatis" if str(ss.get("k_mode", "Otomatis")).startswith("Otomatis") else "manual",
        "setpoint": float(ss.get("k_sp", 45)),
        "target_ka": float(ss.get("k_target", 14.0)),
        "blower_manual": bool(ss.get("k_blower", True)),
        "pemanas_manual": bool(ss.get("k_pemanas", True)),
        "pilihan_cuaca": PILIHAN_CUACA.get(ss.get("k_cuaca"), "skenario"),
    }


def sinkron():
    """Majukan model sampai waktu proses yang setara dengan waktu demo saat ini."""
    d = detik_demo()
    maju_ke(st.session_state.sim, d * JAM_PER_DETIK, kendali())
    if st.session_state.berjalan and d >= DEMO_DETIK:
        st.session_state.detik_akumulasi = float(DEMO_DETIK)
        st.session_state.berjalan = False
        st.session_state.t_mulai = None
        st.rerun(scope="app")
    return d


# ==============================================================================
# SIDEBAR - KONSOL DEMO
# ==============================================================================
with st.sidebar:
    st.markdown("### Konsol demo")
    st.caption("skala 4 menit simulasi = 24 jam proses")
    kol1, kol2 = st.columns(2)
    with kol1:
        if st.session_state.berjalan:
            if st.button("⏸ Jeda", width="stretch"):
                st.session_state.detik_akumulasi = detik_demo()
                st.session_state.berjalan = False
                st.session_state.t_mulai = None
                st.rerun()
        else:
            label = "▶ Mulai" if st.session_state.detik_akumulasi == 0 else "▶ Lanjutkan"
            if st.button(label, width="stretch", type="primary",
                         disabled=st.session_state.detik_akumulasi >= DEMO_DETIK):
                st.session_state.berjalan = True
                st.session_state.t_mulai = time.time()
                st.rerun()
    with kol2:
        if st.button("↺ Reset", width="stretch"):
            reset_demo()
            st.rerun()
    if st.button("⏩ Maju 1 jam proses", width="stretch",
                 disabled=detik_demo() >= DEMO_DETIK):
        st.session_state.detik_akumulasi = min(float(DEMO_DETIK), detik_demo() + 1.0 / JAM_PER_DETIK)
        if st.session_state.berjalan:
            st.session_state.t_mulai = time.time()
        st.rerun()

    st.markdown("---")
    st.markdown("### Cuaca")
    st.selectbox("Kondisi radiasi matahari", list(PILIHAN_CUACA), key="k_cuaca",
                 help="Skenario demo: pagi cerah, 12:00 berawan, 14:00 hujan, 16:00 berawan, "
                      "17:30 cerah, lalu malam. Menunjukkan peralihan energi hibrida secara otomatis.")

    st.markdown("---")
    with st.expander("Panduan Penggunaan Simulasi", expanded=False):
        st.markdown("""
| Demo | Jam proses | Yang ditunjukkan |
|---|---|---|
| 00:00 | 08:00 | Tekan **Mulai**. Tab **Diagram alir**: jelaskan alur tungku batang padi → filter → penukar panas hibrida → rumah pengering, dan PLTS → baterai → blower & IoT |
| 00:30 | 11:00 | Pindah ke **Panel operasional**: KA awal 27,7 %, 3 zona rak, pusat kendali |
| 00:40 | 12:00 | Berawan: buka **Energi hibrida**, daya tungku naik |
| 01:00 | 14:00 | Hujan: suhu rak tetap stabil berkat tungku biomassa |
| 01:40 | 18:00 | Matahari terbenam: listrik dari baterai |
| 02:52 | 01:16 | Rak Bawah mencapai 14 %. Buka **Panel operasional** |
| 03:10 | 03:02 | Baterai di bawah 30 %: hemat energi otomatis |
| 03:20 | 04:00 | Rak Tengah mencapai 14 % |
| 03:40 | 06:01 | Rak Atas selesai: tungku mati otomatis, pendinginan |
| 03:45 | 06:34 | Buka **Log & ekspor**: ringkasan batch dan unduh CSV |

Uji interaktif (singkat, lalu kembalikan): geser setpoint ke 55 °C untuk memicu alarm suhu rak, atau pilih mode manual lalu matikan blower untuk memicu interlock tungku.
""")

# ==============================================================================
# HEADER (diperbarui tiap detik)
# ==============================================================================
berjalan = st.session_state.berjalan
interval = 1.0 if berjalan else None


@st.fragment(run_every=interval)
def header():
    d = sinkron()
    s = st.session_state.sim
    jam_lokal = JAM_MULAI + s["jam"]
    status = ("DEMO BERJALAN" if st.session_state.berjalan else
              ("DEMO SELESAI" if d >= DEMO_DETIK else ("DIJEDA" if d > 0 else "SIAP")))
    warna_status = "#3fb950" if st.session_state.berjalan else "#d19a38"
    html(f"""
    <div class="topbar">
      <div>
        <h1>🌾 SI-PADI - Panel Monitoring Pengering Gabah Padi</h1>
        <p>Rumah pengering hibrida surya-biomassa 1 ton, 3 zona sensor rak, Pusat Organik PUSAKA BLORA, Desa Sidorejo, Kedungtuban, Blora</p>
      </div>
      <div class="chips">
        <div class="chip" style="color:{warna_status};font-weight:700;">{status}</div>
        <div class="chip jam">Jam proses {f1(s['jam'])} / 24</div>
        <div class="chip">Pukul simulasi <b>{format_jam(jam_lokal)}</b></div>
        <div class="chip">Cuaca <b>{CUACA[s['cuaca']]['label'] if s['iradiasi'] > 0 else 'Malam'}</b></div>
        <div class="chip">Demo <b>{int(d)//60:02d}:{int(d)%60:02d}</b> / {DEMO_DETIK // 60:02d}:{DEMO_DETIK % 60:02d}</div>
        <div class="chip">{datetime.now(WIB).strftime('%H:%M:%S')} WIB</div>
      </div>
    </div>
    <div class="demo-bar"><i style="width:{d / DEMO_DETIK * 100:.1f}%"></i></div>
    """)


header()


# ==============================================================================
# GRAFIK (Altair, tema gelap)
# ==============================================================================
def gaya(ch, tinggi=250):
    if tinggi:
        ch = ch.properties(height=tinggi)
    return (ch
            .configure(background="transparent")
            .configure_axis(labelColor="#8890a1", titleColor="#8890a1", gridColor="#1f2431",
                            domainColor="#333a4d", tickColor="#333a4d", labelFontSize=11, titleFontSize=11)
            .configure_legend(labelColor="#c9ccd4", titleColor="#8890a1", orient="bottom", labelFontSize=11)
            .configure_view(strokeWidth=0))


SUMBU_JAM = alt.X("jam:Q", title="Jam proses (4 menit demo = 24 jam)",
                  scale=alt.Scale(domain=[0, 24]), axis=alt.Axis(values=list(range(0, 25, 2))))


def df_riwayat():
    return pd.DataFrame(st.session_state.sim["riwayat"])


def grafik_per_rak(df, awalan, judul_y, domain=None, garis=None, garis_label=None):
    kolom = [f"{awalan}_{z}" for z in URUTAN_TAMPIL]
    panjang = df[["jam"] + kolom].melt("jam", var_name="rak", value_name="nilai")
    panjang["rak"] = panjang["rak"].str.replace(f"{awalan}_", "").map(NAMA_ZONA)
    skala_y = alt.Scale(domain=domain) if domain else alt.Scale(zero=False)
    garis_rak = alt.Chart(panjang).mark_line(strokeWidth=2.2).encode(
        x=SUMBU_JAM,
        y=alt.Y("nilai:Q", title=judul_y, scale=skala_y),
        color=alt.Color("rak:N", title=None,
                        scale=alt.Scale(domain=[NAMA_ZONA[z] for z in URUTAN_TAMPIL],
                                        range=[WARNA_ZONA[z] for z in URUTAN_TAMPIL])),
        tooltip=[alt.Tooltip("jam:Q", title="Jam", format=".1f"), "rak:N",
                 alt.Tooltip("nilai:Q", title=judul_y, format=".1f")],
    )
    lapis = [garis_rak]
    if garis is not None:
        lapis.append(alt.Chart(pd.DataFrame({"y": [garis]})).mark_rule(
            strokeDash=[5, 4], color="#3fb950").encode(y="y:Q"))
        lapis.append(alt.Chart(pd.DataFrame({"y": [garis], "t": [garis_label], "jam": [0.3]})).mark_text(
            align="left", dy=-7, color="#3fb950", fontSize=11).encode(x="jam:Q", y="y:Q", text="t:N"))
    return alt.layer(*lapis)


def legenda(item):
    html('<div style="display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:#c9ccd4;margin:-4px 0 4px 0;">'
         + "".join(f'<span><i style="display:inline-block;width:14px;height:3px;background:{w};'
                   f'vertical-align:middle;margin-right:6px;{"background:repeating-linear-gradient(90deg," + w + " 0 4px,transparent 4px 7px);" if putus else ""}"></i>{t}</span>'
                   for t, w, putus in item) + '</div>')


WARNA_KONDISI = {"Cerah": "#e5a43b", "Berawan": "#8b95a8", "Hujan": "#58a6ff", "Malam": "#0a0b10"}


def latar_cuaca(df):
    """Latar belakang berwarna sesuai kondisi cuaca/malam pada setiap jam proses."""
    d = df[["jam", "cuaca", "iradiasi"]].copy()
    d["kondisi"] = [("Malam" if ir <= 0 else cu) for cu, ir in zip(d["cuaca"], d["iradiasi"])]
    d["warna"] = d["kondisi"].map(WARNA_KONDISI)
    d["jam2"] = d["jam"] + REKAM_TIAP_JAM
    return alt.Chart(d).mark_rect(opacity=0.13).encode(
        x=SUMBU_JAM, x2="jam2:Q", color=alt.Color("warna:N", scale=None, legend=None),
        tooltip=[alt.Tooltip("kondisi:N", title="Kondisi")])


# ==============================================================================
# TAB
# ==============================================================================
tab_hmi, tab_dash, tab_energi, tab_emisi, tab_log, tab_spek = st.tabs([
    "Diagram alir proses (HMI)",
    "Panel operasional",
    "Energi hibrida",
    "Emisi & kualitas udara",
    "Log & ekspor data",
    "Spesifikasi & RAB",
])

# ------------------------------------------------------------------------------
# TAB 1 - PANEL OPERASIONAL
# ------------------------------------------------------------------------------
with tab_dash:
    @st.fragment(run_every=interval)
    def panel_operasional():
        sinkron()
        s = st.session_state.sim
        k = kendali()
        r = ringkasan(s, k["target_ka"])

        if s["fase_akhir"] == "berhenti":
            sisa_teks, sisa_sub = "Selesai", f"batch tuntas pada jam ke-{f1(s['jam_selesai_batch'])}"
        elif s["selesai"]:
            sisa_teks, sisa_sub = "Pendinginan", "tungku mati, blower 30 menit"
        else:
            jam_prediksi = prediksi_selesai(s, k)
            if jam_prediksi is None:
                sisa_teks = "> 30 jam"
                sisa_sub = "target tidak tercapai, periksa blower dan tungku"
            else:
                sisa_teks = f"±{f1(jam_prediksi - s['jam'])} jam"
                sisa_sub = f"selesai sekitar pukul {format_jam(JAM_MULAI + jam_prediksi)}"
        warna_ka = "#3fb950" if r["ka_rata"] <= k["target_ka"] + 0.05 else "#d19a38"
        html(f"""
        <div class="kpi-grid">
          <div class="kpi"><div class="kpi-j">Kadar air rata-rata batch</div>
            <div class="kpi-n" style="color:{warna_ka}">{f1(r['ka_rata'])} %</div>
            <div class="kpi-s">awal {f1(KA_AWAL_WB, 2)} % → target ≤ {f1(k['target_ka'])} % (bb)</div></div>
          <div class="kpi"><div class="kpi-j">Rak mencapai target</div>
            <div class="kpi-n" style="color:#f1f3f7">{r['selesai']} / 3</div>
            <div class="kpi-s">{'semua rak siap dibongkar' if r['selesai'] == 3 else 'rak bawah kering lebih dulu'}</div></div>
          <div class="kpi"><div class="kpi-j">Sisa waktu pengeringan</div>
            <div class="kpi-n" style="color:#f1f3f7">{sisa_teks}</div>
            <div class="kpi-s">{sisa_sub}</div></div>
          <div class="kpi"><div class="kpi-j">Air sudah diuapkan</div>
            <div class="kpi-n" style="color:#58a6ff">{f1(r['air_menguap'], 0)} kg</div>
            <div class="kpi-s">berat gabah kini {f1(r['massa'], 0)} kg</div></div>
          <div class="kpi"><div class="kpi-j">Suhu udara masuk ruang</div>
            <div class="kpi-n" style="color:#ff7b72">{f1(s['t_masuk'])} °C</div>
            <div class="kpi-s">setpoint {f1(k['setpoint'], 0)} °C, udara luar {f1(s['t_amb'])} °C</div></div>
        </div>
        """)

        kiri, kanan = st.columns([2.35, 1])

        # ---- Kabinet rak ---------------------------------------------------
        with kiri:
            baris_rak = ""
            for z in URUTAN_TAMPIL:
                d = s["zona"][z]
                ka = db_ke_wb(d["ka_db"])
                kemajuan = max(0.0, min(1.0, (KA_AWAL_ZONA[z] - ka) / max(0.1, KA_AWAL_ZONA[z] - k["target_ka"])))
                if d["status"] == "Selesai":
                    pill, teks_pill = "selesai", "Selesai"
                elif s["blower"] == 0:
                    pill, teks_pill = "henti", "Tertahan"
                else:
                    pill, teks_pill = "proses", "Proses"
                warna_ka_rak = "#3fb950" if d["status"] == "Selesai" else "#f1f3f7"
                baris_rak += f"""
                <div class="rak" style="--c:{WARNA_ZONA[z]}">
                  <div class="rak-nama">{NAMA_ZONA[z]}<small>Zona {NOMOR_ZONA[z]}</small></div>
                  <div class="ukur"><label>Suhu</label><b>{f1(d['suhu'])} °C</b></div>
                  <div class="ukur"><label>RH</label><b>{f1(d['rh'], 0)} %</b></div>
                  <div class="ukur"><label>Laju</label><b>{'-' if d['laju'] <= 0 else '−' + f1(d['laju'], 2)}</b><label>%/jam</label></div>
                  <div class="ka"><b style="color:{warna_ka_rak}">{f1(ka)} %</b>
                    <div class="bar"><i style="width:{kemajuan * 100:.0f}%;background:{WARNA_ZONA[z]}"></i></div>
                    <small>{kemajuan * 100:.0f} % menuju {f1(k['target_ka'])} %</small></div>
                  <div class="pill {pill}">{teks_pill}</div>
                </div>"""
            rh_atas = s["zona"]["atas"]["rh"]
            html(f"""
            <div class="kabinet">
              <div class="aliran"><span>udara panas masuk dari bawah ↑</span></div>
              <div class="rak-list">
                <div class="ventilasi">↑ Udara lembap keluar lewat atap, RH {f1(rh_atas, 0)} %</div>
                {baris_rak}
              </div>
            </div>""")

            df = df_riwayat()
            st.markdown("##### Penurunan kadar air tiap rak")
            st.altair_chart(gaya(grafik_per_rak(df, "ka", "Kadar air (% bb)", [12, 29],
                                                k["target_ka"], f"Target {f1(k['target_ka'])} %"), 270),
                            width="stretch")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("##### Suhu rak")
                st.altair_chart(gaya(grafik_per_rak(df, "suhu", "°C", [20, 60],
                                                    k["setpoint"], f"Setpoint {f1(k['setpoint'], 0)} °C"), 200),
                                width="stretch")
            with g2:
                st.markdown("##### Kelembapan relatif rak")
                st.altair_chart(gaya(grafik_per_rak(df, "rh", "RH (%)", [0, 100]), 200),
                                width="stretch")

        # ---- Pusat kendali -------------------------------------------------
        with kanan:
            with st.container(border=True):
                html('<div class="panel-j">Pusat kendali unit 1 ton</div>')
                st.radio("Mode pengendalian", ["Otomatis (PID)", "Manual"], key="k_mode", horizontal=True)
                st.slider("Setpoint suhu udara pengering (°C)", 38, 55, key="k_sp",
                          help=f"Alarm muncul bila suhu rak > {T_MAKS_GABAH:.0f} °C (risiko gabah retak).")
                st.slider("Target kadar air akhir (% bb)", 12.0, 15.0, step=0.5, key="k_target", format="%.1f",
                          disabled=s["selesai"],
                          help="Gabah kering giling umumnya ≤ 14 %.")
                if k["mode"] == "manual":
                    t1, t2 = st.columns(2)
                    with t1:
                        st.toggle("Blower", key="k_blower")
                    with t2:
                        st.toggle("Tungku", key="k_pemanas")
                    st.caption("Tanpa blower, tungku otomatis dikunci (interlock).")
                sumber_panas = ("Surya + biomassa" if s["firing"] > 0.05 and s["iradiasi"] > 50 else
                                "Biomassa" if s["firing"] > 0.05 else
                                "Surya (rumah kaca)" if s["iradiasi"] > 50 else "-")
                html(f"""
                <div class="akt">
                  <div>Blower<b>{'MATI' if s['blower'] == 0 else f"{s['blower'] * 100:.0f} %"}</b></div>
                  <div>Daya tungku<b>{s['firing'] * 100:.0f} %</b></div>
                  <div>Sumber panas<b>{sumber_panas}</b></div>
                  <div>Listrik<b>{s['sumber_listrik']}</b></div>
                </div>""")

            with st.container(border=True):
                html('<div class="panel-j">Alarm aktif</div>')
                aktif = []
                peta = {
                    "interlock": ("Kritis", "Blower mati, tungku dikunci"),
                    "panas": ("Kritis", f"Suhu rak > {T_MAKS_GABAH:.0f} °C"),
                    "timeout": ("Kritis", "24 jam tercapai, KA belum di target"),
                    "pemanas_off": ("Peringatan", "Tungku mati, pengeringan melambat"),
                    "hemat": ("Peringatan", "Hemat energi, blower 70 %"),
                    "selisih": ("Peringatan", "Selisih KA antar rak > 5 %"),
                    "co": ("Peringatan", f"CO gas buang > {AMBANG_CO:.0f} mg/Nm³"),
                    "pm": ("Peringatan", f"Partikulat > {AMBANG_PM:.0f} mg/Nm³"),
                    "filter": ("Peringatan", "Tekanan filter tinggi"),
                }
                for kunci, (tingkat, teks) in peta.items():
                    if s["flag"].get(kunci):
                        aktif.append(f'<div class="alarm {tingkat}">{teks}</div>')
                if s["sumber_listrik"] == "Grid":
                    aktif.append('<div class="alarm Peringatan">Suplai dari cadangan jaringan</div>')
                html("".join(aktif) if aktif else '<div class="alarm ok">Semua parameter normal</div>')
                html('<div class="panel-j" style="margin-top:10px;font-size:13px;">Kejadian terakhir</div>')
                html("".join(f'<div class="logi"><b>{e["Jam lokal"]}</b> {e["Kejadian"]}</div>'
                             for e in reversed(s["log"][-5:])))

    panel_operasional()

# ------------------------------------------------------------------------------
# TAB 2 - ENERGI HIBRIDA
# ------------------------------------------------------------------------------
with tab_energi:
    @st.fragment(run_every=interval)
    def panel_energi():
        sinkron()
        s = st.session_state.sim
        laju_bio = s["firing"] * Q_TUNGKU_MAKS_KW * 3.6 / (LHV_JERAMI * EFISIENSI_TUNGKU_HE)
        porsi_surya = 12.0 * s["iradiasi"] / 1000.0
        porsi_bio = max(0.0, s["t_masuk"] - s["t_amb"] - porsi_surya)
        total_naik = max(0.1, porsi_surya + porsi_bio)
        html(f"""
        <div class="kpi-grid">
          <div class="kpi"><div class="kpi-j">Daya PLTS (4.000 Wp)</div>
            <div class="kpi-n" style="color:#58a6ff">{f1(s['p_pv'], 0)} W</div>
            <div class="kpi-s">iradiasi {f1(s['iradiasi'], 0)} W/m², {('cuaca ' + CUACA[s['cuaca']]['label'].lower()) if s['iradiasi'] > 0 else 'malam hari'}</div></div>
          <div class="kpi"><div class="kpi-j">Baterai ({f1(BATERAI_KWH, 0)} kWh)</div>
            <div class="kpi-n" style="color:{'#3fb950' if s['soc'] >= SOC_HEMAT else '#e5a43b'}">{f1(s['soc'], 0)} %</div>
            <div class="kpi-s">mode {s['mode_energi'].lower()}, sumber listrik {s['sumber_listrik']}</div></div>
          <div class="kpi"><div class="kpi-j">Beban listrik</div>
            <div class="kpi-n" style="color:#f1f3f7">{f1(s['p_beban'], 0)} W</div>
            <div class="kpi-s">blower, IoT, lampu, fan tungku</div></div>
          <div class="kpi"><div class="kpi-j">Konsumsi batang padi</div>
            <div class="kpi-n" style="color:#ff7b72">{f1(laju_bio)} kg/jam</div>
            <div class="kpi-s">total {f1(s['kg_biomassa'], 0)} kg, ruang bakar {f1(s['t_tungku'], 0)} °C</div></div>
          <div class="kpi"><div class="kpi-j">Panas dari surya</div>
            <div class="kpi-n" style="color:#e5a43b">{porsi_surya / total_naik * 100:.0f}% surya</div>
            <div class="kpi-s">sisanya {porsi_bio / total_naik * 100:.0f} % dari biomassa</div></div>
        </div>""")
        df = df_riwayat()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Neraca listrik PLTS, beban, dan baterai")
            daya = df[["jam", "p_pv", "p_beban"]].melt("jam", var_name="seri", value_name="nilai")
            daya["seri"] = daya["seri"].map({"p_pv": "Produksi PLTS (W)", "p_beban": "Beban (W)"})
            skala_warna = alt.Scale(domain=["Produksi PLTS (W)", "Beban (W)", "SOC baterai (%)"],
                                    range=["#58a6ff", "#c9ccd4", "#3fb950"])
            g_daya = alt.Chart(daya).mark_line(strokeWidth=2).encode(
                x=SUMBU_JAM, y=alt.Y("nilai:Q", title="Daya (W)", scale=alt.Scale(domain=[0, 3400])),
                color=alt.Color("seri:N", title=None, scale=skala_warna, legend=None))
            g_soc = alt.Chart(df.assign(seri="SOC baterai (%)")).mark_line(strokeDash=[5, 3], strokeWidth=2).encode(
                x=SUMBU_JAM, y=alt.Y("soc:Q", title="SOC baterai (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("seri:N", title=None, scale=skala_warna, legend=None))
            legenda([("Produksi PLTS (W)", "#58a6ff", False), ("Beban (W)", "#c9ccd4", False),
                     ("SOC baterai (%)", "#3fb950", True)])
            st.altair_chart(gaya(alt.layer(latar_cuaca(df), g_daya, g_soc).resolve_scale(y="independent", color="independent"), 260),
                            width="stretch")
            st.caption(f"Warna latar: jingga cerah, abu-abu berawan, biru hujan, gelap malam. "
                       f"PLTS menghasilkan {f1(s['kwh_pv'])} kWh, beban memakai {f1(s['kwh_beban'])} kWh, "
                       f"jaringan PLN {f1(s['kwh_grid'])} kWh.")
        with c2:
            st.markdown("##### Daya tungku dan suhu udara")
            g_fir = alt.Chart(df).mark_area(opacity=0.30, color="#ff7b72").encode(
                x=SUMBU_JAM, y=alt.Y("firing:Q", title="Daya tungku (%)",
                                     scale=alt.Scale(domain=[0, 100])))
            suhu = df[["jam", "t_masuk", "t_amb"]].melt("jam", var_name="seri", value_name="suhu")
            suhu["seri"] = suhu["seri"].map({"t_masuk": "Udara masuk ruang (°C)", "t_amb": "Udara luar (°C)"})
            g_suhu = alt.Chart(suhu).mark_line(strokeWidth=2).encode(
                x=SUMBU_JAM, y=alt.Y("suhu:Q", title="Suhu (°C)", scale=alt.Scale(domain=[15, 60])),
                color=alt.Color("seri:N", title=None,
                                scale=alt.Scale(domain=["Udara masuk ruang (°C)", "Udara luar (°C)"],
                                                range=["#d19a38", "#8890a1"]), legend=None))
            legenda([("Udara masuk ruang (°C)", "#d19a38", False), ("Udara luar (°C)", "#8890a1", False),
                     ("Daya tungku (%)", "#ff7b72", False)])
            st.altair_chart(gaya(alt.layer(latar_cuaca(df), g_fir, g_suhu).resolve_scale(y="independent", color="independent"), 260),
                            width="stretch")
            st.caption("Siang hari, atap polikarbonat ikut memanaskan udara sehingga daya tungku turun. "
                       "Saat hujan dan malam, tungku biomassa mengambil alih.")
        r = ringkasan(s, kendali()["target_ka"])
        html(f"""<div class="catatan" style="margin-bottom:8px;">Capaian batch ini: <b>listrik {f1(r['porsi_listrik_pv'], 0)} % dari PLTS</b>,
        <b>energi terbarukan {f1(r['porsi_terbarukan'], 1)} %</b>, energi fosil {f1(100 - r['porsi_terbarukan'], 1)} %.</div>""")
        html(f"""<div class="catatan"><b>Panas</b> pengeringan berasal dari atap polikarbonat dan tungku batang padi melalui
        penukar panas, sehingga gabah tidak terkena gas buang. <b>Listrik</b> untuk blower, sensor, lampu, dan fan
        tungku berasal dari PLTS dan baterai. Jaringan PLN hanya cadangan saat baterai di bawah {SOC_GRID:.0f} %.</div>""")

    panel_energi()

# ------------------------------------------------------------------------------
# TAB 3 - EMISI & KUALITAS UDARA
# ------------------------------------------------------------------------------
with tab_emisi:
    @st.fragment(run_every=interval)
    def panel_emisi():
        sinkron()
        s = st.session_state.sim
        r = ringkasan(s, kendali()["target_ka"])
        rng = random.Random(int(s["jam"] * 50))
        co_ruang = 0.6 + rng.uniform(0, 0.6)
        pm_luar = 24 + rng.uniform(-3, 3)
        html(f"""
        <div class="kpi-grid">
          <div class="kpi"><div class="kpi-j">CO gas buang (cerobong)</div>
            <div class="kpi-n" style="color:{'#ff7b72' if s['co'] > AMBANG_CO else '#3fb950'}">{f1(s['co'], 0)}</div>
            <div class="kpi-s">mg/Nm³, ambang alarm {AMBANG_CO:.0f}</div></div>
          <div class="kpi"><div class="kpi-j">Partikulat setelah filter</div>
            <div class="kpi-n" style="color:{'#ff7b72' if s['pm'] > AMBANG_PM else '#3fb950'}">{f1(s['pm'])}</div>
            <div class="kpi-s">mg/Nm³, ambang alarm {AMBANG_PM:.0f}</div></div>
          <div class="kpi"><div class="kpi-j">Beda tekanan filter</div>
            <div class="kpi-n" style="color:{'#e5a43b' if s['dp_filter'] > AMBANG_DP_FILTER else '#f1f3f7'}">{f1(s['dp_filter'], 0)} Pa</div>
            <div class="kpi-s">bersihkan filter bila di atas {AMBANG_DP_FILTER:.0f} Pa</div></div>
          <div class="kpi"><div class="kpi-j">Efektivitas penukar panas</div>
            <div class="kpi-n" style="color:#f1f3f7">{f1(s['eff_he'] * 100, 0)} %</div>
            <div class="kpi-s">gas masuk {f1(s['t_gas_he'], 0)} °C, keluar {f1(s['t_cerobong'], 0)} °C</div></div>
          <div class="kpi"><div class="kpi-j">CO di ruang pengering</div>
            <div class="kpi-n" style="color:#3fb950">{f1(co_ruang)} ppm</div>
            <div class="kpi-s">setara udara luar, bebas gas buang</div></div>
        </div>""")
        df = df_riwayat()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### CO gas buang")
            g = alt.layer(
                alt.Chart(df).mark_line(color="#e5a43b", strokeWidth=2).encode(
                    x=SUMBU_JAM, y=alt.Y("co:Q", title="mg/Nm³", scale=alt.Scale(domain=[0, 700]))),
                alt.Chart(pd.DataFrame({"y": [AMBANG_CO]})).mark_rule(strokeDash=[5, 4], color="#ff7b72").encode(y="y:Q"))
            st.altair_chart(gaya(g, 210), width="stretch")
        with c2:
            st.markdown("##### Partikulat gas buang setelah filter")
            g = alt.layer(
                alt.Chart(df).mark_line(color="#58a6ff", strokeWidth=2).encode(
                    x=SUMBU_JAM, y=alt.Y("pm:Q", title="mg/Nm³", scale=alt.Scale(domain=[0, 60]))),
                alt.Chart(pd.DataFrame({"y": [AMBANG_PM]})).mark_rule(strokeDash=[5, 4], color="#ff7b72").encode(y="y:Q"))
            st.altair_chart(gaya(g, 210), width="stretch")
        html(f"""<div class="catatan">PM2.5 udara masuk ±{f1(pm_luar, 0)} µg/m³. Batch ini menghindari
        <b>±{f1(r['co2_dihindari'], 0)} kg CO₂</b> dibanding pengering LPG dan listrik PLN.
        Ambang alarm masih setelan internal dan akan disesuaikan dengan baku mutu Permen LHK P.11/2021
        setelah uji emisi lapangan.</div>""")

    panel_emisi()


# ------------------------------------------------------------------------------
# TAB 4 - DIAGRAM ALIR PROSES (HMI)
# ------------------------------------------------------------------------------
def svg_hmi(s, k):
    """Diagram alir hidup. Hanya angka & kelas yang berubah tiap detik, sehingga animasi CSS
    (aliran garis putus-putus, kipas blower, api tungku) tetap berjalan tanpa terulang."""
    WG, WF, WB, WU, WP, WL, WD, WT = ("#e8743b", "#d19a38", "#3fb950", "#58a6ff",
                                      "#ff7b72", "#f2cc60", "#b392f0", "#a47148")

    def laju(nilai, cepat, sedang, ambang=0.02):
        if nilai <= ambang:
            return "mati"
        return "cepat" if nilai >= cepat else ("sedang" if nilai >= sedang else "lambat")

    k_gas = laju(s["firing"], 0.6, 0.25)
    k_udara = laju(s["blower"], 0.95, 0.5)
    k_pv = laju(s["p_pv"], 1500, 300, 20)
    k_beban = laju(s["p_beban"], 800, 200, 5)
    k_grid = "sedang" if s["sumber_listrik"] == "Grid" else "mati"
    k_bat = "mati" if s["p_pv"] <= 20 else k_pv
    kipas_on = s["blower"] > 0
    api_on = s["firing"] > 0.02
    massa = ringkasan(s, k["target_ka"])["massa"]

    def aliran(d, warna, kelas, panah=True):
        w_panah = "#3a4052" if kelas == "mati" else warna
        mk = f' marker-end="url(#m-{w_panah[1:]})"' if panah else ""
        return (f'<path class="pipa" d="{d}"/>'
                f'<path class="alir {kelas}" d="{d}" stroke="{warna}"{mk}/>')

    def marker(w):
        return (f'<marker id="m-{w[1:]}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="11" '
                f'markerHeight="11" markerUnits="userSpaceOnUse" orient="auto">'
                f'<path d="M0 1L9 5L0 9z" fill="{w}"/></marker>')

    rak = ""
    for i, z in enumerate(URUTAN_TAMPIL):
        d = s["zona"][z]
        y = 172 + i * 70
        w = WB if d["status"] == "Selesai" else WARNA_ZONA[z]
        rak += (f'<rect x="590" y="{y}" width="170" height="58" rx="5" fill="#0f1015" stroke="{w}" stroke-width="1.6"/>'
                f'<text x="600" y="{y + 18}" fill="#e2e4e9" font-size="11.5" font-weight="700">{NAMA_ZONA[z]} (Zona {NOMOR_ZONA[z]})</text>'
                f'<text x="600" y="{y + 37}" fill="{w}" font-size="13" font-weight="700">KA {f1(db_ke_wb(d["ka_db"]))} %</text>'
                f'<text x="752" y="{y + 37}" fill="#c9ccd4" font-size="10.5" text-anchor="end">{f1(d["suhu"])} °C  RH {f1(d["rh"], 0)} %</text>'
                f'<text x="600" y="{y + 51}" fill="#697184" font-size="9.5">{d["status"]}</text>')

    api = ""
    if api_on:
        for dx, h in ((-18, 16), (0, 22), (18, 15)):
            cx = 102 + dx
            api += (f'<path class="api" d="M{cx - 7} 402 Q{cx - 8} {402 - h * 0.6} {cx} {402 - h} '
                    f'Q{cx + 8} {402 - h * 0.6} {cx + 7} 402 Z" fill="{WG}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 600" font-family="Segoe UI, Roboto, Helvetica, Arial, sans-serif">
<defs>{''.join(marker(w) for w in (WG, WF, WB, WU, WP, WL, WD, WT, "#8890a1", "#3a4052"))}</defs>
<rect width="1120" height="600" rx="10" fill="#12141c"/>
<rect x="14" y="14" width="780" height="572" rx="8" fill="#161822" stroke="#2b3246"/>
<text x="30" y="40" fill="#e2e4e9" font-size="13" font-weight="700">Stasiun bioenergi, pembersihan gas &amp; rumah pengering</text>

<!-- aliran gas: tungku -> heat riser -> filter -> penukar panas -> cerobong -->
{aliran("M102 574 L102 504", WT, k_gas)}
<text x="114" y="580" fill="{WT}" font-size="10">umpan batang padi</text>
{aliran("M168 470 L218 470 L218 368", WG, k_gas, panah=False)}
{aliran("M218 326 L218 298", WF, k_gas, panah=False)}
{aliran("M218 250 L218 70 L345 70 L345 250 L445 250 L445 280 L365 280 L365 310 L445 310 L445 340 L365 340 L365 370 L465 370 L465 152", WF, k_gas, panah=False)}
{aliran("M465 150 L465 58", WB, k_gas)}
<text x="478" y="38" fill="{WB}" font-size="10.5" font-weight="600">Gas buang: CO {f1(s['co'], 0)} mg/Nm³, PM {f1(s['pm'])} mg/Nm³</text>
<text x="478" y="52" fill="#697184" font-size="9.5">cerobong {f1(s['t_cerobong'], 0)} °C</text>

<!-- aliran udara: udara luar -> penukar panas -> blower -> plenum rumah pengering -->
{aliran("M290 556 L405 556 L405 424", WU, k_udara)}
<text x="282" y="552" fill="#8890a1" font-size="10" text-anchor="end">Udara luar {f1(s['t_amb'])} °C, RH {f1(s['rh_amb'], 0)} %</text>
<text x="282" y="566" fill="#697184" font-size="9.5" text-anchor="end">sensor kualitas udara masuk</text>
{aliran("M482 396 L522 396 L522 522 L557 522", WP, k_udara)}
<text x="490" y="388" fill="{WP if kipas_on else '#697184'}" font-size="11" font-weight="700">{f1(s['t_masuk'])} °C</text>
<circle cx="522" cy="462" r="17" fill="#12141c" stroke="{WP if kipas_on else '#3a4052'}" stroke-width="2"/>
<g class="kipas{'' if kipas_on else ' diam'}" style="animation-duration:{0.5 if s['blower'] >= 0.95 else 0.9}s">
<path d="M522 462 L522 449 A6 6 0 0 1 531 455 Z M522 462 L535 462 A6 6 0 0 1 529 471 Z M522 462 L522 475 A6 6 0 0 1 513 469 Z M522 462 L509 462 A6 6 0 0 1 515 453 Z" fill="{WP if kipas_on else '#3a4052'}"/>
</g>

<!-- tungku -->
<rect x="36" y="330" width="132" height="172" rx="6" fill="#1d202d" stroke="{WF if api_on else '#3a4052'}" stroke-width="2"/>
<text x="102" y="352" fill="{WF if api_on else '#697184'}" font-size="12" font-weight="700" text-anchor="middle">Tungku biomassa</text>
<text x="102" y="367" fill="#8890a1" font-size="10" text-anchor="middle">batang padi</text>
{api}
<rect x="48" y="408" width="108" height="42" rx="4" fill="#0f1015" stroke="#333a4d"/>
<text x="102" y="436" fill="{WP if api_on else '#697184'}" font-size="18" font-weight="700" text-anchor="middle">{f1(s['t_tungku'], 0)} °C</text>
<text x="102" y="470" fill="#c9ccd4" font-size="11" text-anchor="middle">Daya {s['firing'] * 100:.0f} %</text>
<text x="102" y="487" fill="#8890a1" font-size="10" text-anchor="middle">terpakai {f1(s['kg_biomassa'], 0)} kg</text>

<!-- heat riser & filter -->
<rect x="200" y="100" width="90" height="400" rx="6" fill="#1a1d29" fill-opacity="0.55" stroke="#8890a1" stroke-width="1.4"/>
<rect x="200" y="328" width="90" height="38" fill="#232838" stroke="#333a4d"/>
<text x="258" y="351" fill="{WF}" font-size="10" font-weight="600" text-anchor="middle">Filter kasar</text>
<rect x="200" y="252" width="90" height="44" fill="#232838" stroke="#333a4d"/>
<text x="258" y="270" fill="{WB}" font-size="10" font-weight="600" text-anchor="middle">Filter halus</text>
<text x="258" y="285" fill="{WB}" font-size="9.5" text-anchor="middle">HEPA &amp; gas</text>
<text x="258" y="232" fill="#c9ccd4" font-size="10" text-anchor="middle">ΔP {f1(s['dp_filter'], 0)} Pa</text>
<text x="258" y="440" fill="#8890a1" font-size="10" text-anchor="middle">gas panas</text>
<text x="258" y="454" fill="#8890a1" font-size="10" text-anchor="middle">naik</text>
<text x="245" y="520" fill="#e2e4e9" font-size="11" font-weight="700" text-anchor="middle">Heat riser</text>

<!-- penukar panas hibrida -->
<rect x="322" y="150" width="160" height="272" rx="6" fill="#182026" fill-opacity="0.6" stroke="{WB}" stroke-width="2"/>
<text x="405" y="170" fill="{WB}" font-size="11" font-weight="700" text-anchor="middle">Penukar panas</text>
<text x="405" y="184" fill="{WB}" font-size="11" font-weight="700" text-anchor="middle">hibrida</text>
<text x="405" y="208" fill="#e2e4e9" font-size="12.5" font-weight="700" text-anchor="middle">{f1(s['eff_he'] * 100, 0)} %</text>
<text x="405" y="222" fill="#8890a1" font-size="9.5" text-anchor="middle">efektivitas</text>
<text x="405" y="238" fill="#c9ccd4" font-size="9.5" text-anchor="middle">gas masuk {f1(s['t_gas_he'], 0)} °C</text>
<text x="405" y="404" fill="#8890a1" font-size="9.5" text-anchor="middle">udara bersih dipanaskan ↑</text>

<!-- rumah pengering -->
<path d="M560 126 L675 84 L790 126" stroke="{WU}" stroke-width="1.6" fill="none" opacity="0.8"/>
<text x="675" y="116" fill="{WU}" font-size="10" text-anchor="middle">atap polikarbonat +{f1(12 * s['iradiasi'] / 1000)} °C</text>
{aliran("M675 82 L675 64", "#8890a1", k_udara)}
<text x="690" y="70" fill="#8890a1" font-size="10">udara lembap keluar</text>
<text x="690" y="83" fill="#8890a1" font-size="10">RH {f1(s['zona']['atas']['rh'], 0)} %</text>
<rect x="560" y="126" width="230" height="414" rx="6" fill="#1a1c24" stroke="{WF}" stroke-width="2"/>
<text x="675" y="146" fill="{WF}" font-size="12" font-weight="700" text-anchor="middle">Rumah pengering ±6 × 4 × 3 m</text>
<text x="675" y="162" fill="#8890a1" font-size="10" text-anchor="middle">1 ton per batch, udara naik dari bawah</text>
{aliran("M574 512 L574 170", WP, k_udara)}
{aliran("M776 512 L776 170", WP, k_udara)}
{rak}
<text x="675" y="416" fill="{WP if kipas_on else '#697184'}" font-size="11" font-weight="600" text-anchor="middle">Blower {'mati' if not kipas_on else f"{s['blower'] * 100:.0f} %"}</text>
<text x="675" y="434" fill="#c9ccd4" font-size="10.5" text-anchor="middle">Setpoint {k['setpoint']:.0f} °C, mode {k['mode']}</text>
<text x="675" y="452" fill="#8890a1" font-size="10" text-anchor="middle">Massa kini {f1(massa, 0)} kg</text>
<rect x="582" y="496" width="186" height="34" rx="4" fill="#0f1015" stroke="#333a4d"/>
<text x="675" y="517" fill="#8890a1" font-size="10" text-anchor="middle">plenum udara panas</text>
{aliran("M790 470 L800 470 L800 536 L822 536", WD, "lambat")}

<!-- sistem listrik PLTS & IoT -->
<rect x="808" y="14" width="298" height="572" rx="8" fill="#161822" stroke="#2b3246"/>
<text x="824" y="40" fill="#e2e4e9" font-size="13" font-weight="700">Sistem listrik PLTS &amp; IoT</text>
<rect x="824" y="52" width="266" height="80" rx="6" fill="#151d2a" stroke="{WU if k_pv != 'mati' else '#3a4052'}" stroke-width="2"/>
<text x="957" y="74" fill="{WU if k_pv != 'mati' else '#697184'}" font-size="12" font-weight="700" text-anchor="middle">Panel surya 4.000 Wp</text>
<text x="957" y="102" fill="#e2e4e9" font-size="20" font-weight="700" text-anchor="middle">{f1(s['p_pv'], 0)} W</text>
<text x="957" y="122" fill="#8890a1" font-size="10" text-anchor="middle">iradiasi {f1(s['iradiasi'], 0)} W/m²</text>
{aliran("M957 132 L957 156", WL, k_pv)}
<rect x="844" y="158" width="226" height="42" rx="6" fill="#1d202d" stroke="{WF}" stroke-width="1.4"/>
<text x="957" y="184" fill="{WF}" font-size="11.5" font-weight="700" text-anchor="middle">Solar charge controller (MPPT)</text>
{aliran("M957 200 L957 224", WL, k_bat)}
<rect x="844" y="226" width="226" height="64" rx="6" fill="#1d202d" stroke="{WB}" stroke-width="1.4"/>
<text x="957" y="248" fill="{WB}" font-size="11.5" font-weight="700" text-anchor="middle">Baterai {BATERAI_KWH:.0f} kWh</text>
<rect x="866" y="258" width="182" height="12" rx="3" fill="#0f1015" stroke="#333a4d"/>
<rect x="867" y="259" width="{180 * s['soc'] / 100:.0f}" height="10" rx="2" fill="{WB if s['soc'] >= SOC_HEMAT else WF}"/>
<text x="957" y="285" fill="#e2e4e9" font-size="11" text-anchor="middle">SOC {f1(s['soc'], 0)} %</text>
{aliran("M915 290 L915 378", WL, k_beban)}
<rect x="980" y="306" width="110" height="46" rx="6" fill="#0f1015" stroke="{WF if k_grid != 'mati' else '#2b3246'}" stroke-dasharray="{'0' if k_grid != 'mati' else '4 3'}"/>
<text x="1035" y="325" fill="{WF if k_grid != 'mati' else '#697184'}" font-size="10.5" text-anchor="middle">Jaringan PLN</text>
<text x="1035" y="341" fill="{WF if k_grid != 'mati' else '#697184'}" font-size="10" text-anchor="middle">{'AKTIF' if k_grid != 'mati' else 'cadangan, siaga'}</text>
{aliran("M1035 352 L1035 378", WL, k_grid)}
<rect x="824" y="380" width="266" height="104" rx="6" fill="#0f1015" stroke="#2b3246"/>
<text x="838" y="400" fill="#8890a1" font-size="10.5" font-weight="600">Beban listrik {f1(s['p_beban'], 0)} W</text>
<text x="838" y="420" fill="#e2e4e9" font-size="11">• 2 blower DC: {'mati' if not kipas_on else f"{f1(P_BLOWER_MAKS_W * s['blower'] ** 3, 0)} W"}</text>
<text x="838" y="438" fill="#e2e4e9" font-size="11">• Mikrokontroler, sensor, gateway: {P_IOT_W:.0f} W</text>
<text x="838" y="456" fill="#e2e4e9" font-size="11">• Fan udara tungku: {'aktif' if api_on else 'mati'}</text>
<text x="838" y="474" fill="#e2e4e9" font-size="11">• Lampu: {'menyala' if s['iradiasi'] <= 0 else 'mati'}</text>
<rect x="824" y="500" width="266" height="72" rx="6" fill="#0f1015" stroke="{WD}" stroke-opacity="0.6"/>
<text x="838" y="522" fill="{WD}" font-size="11" font-weight="700">Data logger &amp; server lokal</text>
<text x="838" y="540" fill="#c9ccd4" font-size="10.5">sensor suhu, RH, KA, emisi, energi</text>
<text x="838" y="558" fill="#8890a1" font-size="10.5">→ internet → dasbor web &amp; aplikasi seluler</text>
</svg>"""


LEGENDA_HMI = [("Gas panas dari tungku", "#e8743b"), ("Gas tersaring", "#d19a38"), ("Gas buang bersih", "#3fb950"),
               ("Udara luar", "#58a6ff"), ("Udara panas bersih", "#ff7b72"), ("Listrik", "#f2cc60"),
               ("Data sensor", "#b392f0"), ("Batang padi", "#a47148")]


with tab_hmi:
    @st.fragment(run_every=interval)
    def panel_hmi():
        sinkron()
        s = st.session_state.sim
        html('<div style="display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#c9ccd4;margin:0 0 8px 0;">'
             + "".join(f'<span><i style="display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:6px;'
                       f'background:repeating-linear-gradient(90deg,{w} 0 6px,transparent 6px 10px);"></i>{t}</span>'
                       for t, w in LEGENDA_HMI) + '</div>')
        kelas = "hmi" if st.session_state.berjalan else "hmi jeda"
        st.markdown(f'<div class="{kelas}">' + " ".join(svg_hmi(s, kendali()).split("\n")) + "</div>",
                    unsafe_allow_html=True)
        st.caption("Garis bergerak searah aliran. Makin cepat gerakannya, makin besar lajunya. "
                   "Abu-abu berarti aliran berhenti.")

    panel_hmi()

# ------------------------------------------------------------------------------
# TAB 5 - LOG & EKSPOR
# ------------------------------------------------------------------------------
with tab_log:
    @st.fragment(run_every=interval)
    def panel_log():
        sinkron()
        s = st.session_state.sim
        k = kendali()
        r = ringkasan(s, k["target_ka"])
        if s["fase_akhir"] == "berhenti":
            st.success(f"Batch selesai dalam {f1(s['jam_selesai_batch'])} jam proses "
                       f"(pukul {format_jam(JAM_MULAI + s['jam_selesai_batch'])}).")
            rows = [{"Parameter": f"KA akhir {NAMA_ZONA[z]}",
                     "Nilai": f"{f1(db_ke_wb(s['zona'][z]['ka_db']))} % (jam ke-{f1(s['zona'][z]['jam_selesai'])})"}
                    for z in URUTAN_TAMPIL]
            rows += [
                {"Parameter": "Air diuapkan", "Nilai": f"{f1(r['air_menguap'], 0)} kg"},
                {"Parameter": "Gabah kering", "Nilai": f"{f1(r['massa'], 0)} kg"},
                {"Parameter": "Biomassa batang padi terpakai", "Nilai": f"{f1(s['kg_biomassa'], 0)} kg"},
                {"Parameter": "Energi panas ke udara", "Nilai": f"{f1(s['mj_panas'], 0)} MJ "
                                                                  f"({f1(s['mj_panas'] / max(1, r['air_menguap']))} MJ/kg air)"},
                {"Parameter": "Listrik PLTS / konsumsi / jaringan",
                 "Nilai": f"{f1(s['kwh_pv'])} / {f1(s['kwh_beban'])} / {f1(s['kwh_grid'])} kWh"},
                {"Parameter": "Porsi energi terbarukan / listrik dari PLTS",
                 "Nilai": f"{f1(r['porsi_terbarukan'], 1)} % / {f1(r['porsi_listrik_pv'], 0)} %"},
                {"Parameter": "CO₂ fosil yang dihindari", "Nilai": f"{f1(r['co2_dihindari'], 0)} kg"},
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.info("Ringkasan batch tampil setelah semua rak mencapai target.")

        st.markdown("##### Log kejadian")
        log = pd.DataFrame(s["log"][::-1])
        log["Jam proses"] = log["Jam proses"].map(lambda x: f1(x, 2))
        st.dataframe(log, hide_index=True, width="stretch", height=300)

        df = df_riwayat()
        e1, e2 = st.columns(2)
        with e1:
            st.download_button("Unduh telemetri batch (.csv)", df.to_csv(index=False).encode("utf-8"),
                               file_name="sipadi_telemetri_batch_1ton.csv", mime="text/csv",
                               width="stretch")
        with e2:
            st.download_button("Unduh log kejadian (.csv)", log.to_csv(index=False).encode("utf-8"),
                               file_name="sipadi_log_kejadian.csv", mime="text/csv",
                               width="stretch")
        st.caption("Data direkam tiap 6 menit proses untuk ketiga rak, energi, dan emisi.")

    panel_log()

# ------------------------------------------------------------------------------
# TAB 6 - SPESIFIKASI & RAB (statis)
# ------------------------------------------------------------------------------
with tab_spek:
    def sek(judul, sub="", pertama=False):
        html(f'<div class="sek-j{" pertama" if pertama else ""}">{judul}</div>'
             + (f'<div class="sek-s">{sub}</div>' if sub else ""))

    def tabel(baris, kolom, lebar_kiri="28%"):
        kepala = (f'<tr><th style="width:{lebar_kiri}">{kolom[0]}</th><th>{kolom[1]}</th></tr>')
        isi = "".join(f'<tr><td class="kiri">{k}</td><td>{v}</td></tr>' for k, v in baris)
        html(f'<div class="spek-wrap"><table class="spek"><thead>{kepala}</thead><tbody>{isi}</tbody></table></div>')

    sek("Spesifikasi teknik", "Rancangan unit pengering SI-PADI kapasitas 1 ton per batch.", pertama=True)
    tabel([
        ("Dimensi dan kapasitas", "Rumah pengering ±6 m × 4 m × 3 m, kapasitas ±1 ton gabah basah per siklus"),
        ("Sumber listrik", "PLTS on-grid/off-grid hybrid ±4.000 Wp dengan baterai penyimpanan sebagai cadangan"),
        ("Sumber panas", "Tungku biomassa limbah batang padi → heat riser → filter kasar dan HEPA → penukar panas hibrida → udara bersih ke ruang pengering"),
        ("Beban listrik PLTS", "Blower, lampu, pembakar, sensor, dan sistem IoT"),
        ("Material utama", "Rangka baja ringan galvanis, atap dan dinding polikarbonat UV-protected (efek rumah kaca), lantai rak jaring stainless steel"),
        ("Output", "±1 ton gabah kering (KA ±14 %) per siklus 18-24 jam"),
        ("Hasil uji", "KA 27,72 % bb menjadi 14 % bb dalam 24 jam (±1 ton per batch)"),
        ("Pemantauan", "Sensor → data logger dan server lokal → internet → dasbor web dan aplikasi seluler, lengkap dengan peringatan dan evaluasi kinerja"),
        ("Operasional dan perawatan", "Pembersihan panel berkala, cek sensor bulanan, kalibrasi tiap 6 bulan, dioperasikan 1 operator terlatih"),
        ("Tingkat kesiapan teknologi", "TKT 6-7"),
        ("Acuan", "SNI 6128:2020, pedoman pascapanen padi Kementan, SNI 6729 (pertanian organik), dan regulasi EBT"),
        ("Pengendalian emisi", "Baku mutu emisi sumber tidak bergerak (Permen LHK P.11/2021) dengan pemeriksaan berkala"),
    ], ("Parameter", "Keterangan"))

    rab = pd.DataFrame([
        ["A. Peralatan dan bahan utama", "Kolektor surya", "2 unit", 20_000_000],
        ["A. Peralatan dan bahan utama", "Pompa", "2 unit", 10_000_000],
        ["A. Peralatan dan bahan utama", "Rumah pengering", "1 unit", 15_000_000],
        ["A. Peralatan dan bahan utama", "Tungku biomassa", "1 unit", 15_000_000],
        ["A. Peralatan dan bahan utama", "Pipa stainless steel", "40 meter", 8_000_000],
        ["A. Peralatan dan bahan utama", "Blower", "2 unit", 10_000_000],
        ["A. Peralatan dan bahan utama", "Filter kasar", "1 unit", 1_000_000],
        ["A. Peralatan dan bahan utama", "Filter halus", "1 unit", 1_000_000],
        ["A. Peralatan dan bahan utama", "Valve", "10 unit", 1_000_000],
        ["B. Instalasi dan konstruksi", "Pondasi dan struktur rumah pengering", "1 paket", 20_000_000],
        ["B. Instalasi dan konstruksi", "Instalasi kelistrikan PLTS dan sistem IoT", "1 paket", 10_000_000],
        ["B. Instalasi dan konstruksi", "Sirkulasi udara dan ducting", "1 paket", 8_000_000],
        ["C. Tenaga kerja dan jasa", "Tukang dan instalatur (3 orang × 20 hari)", "60 HOK", 9_000_000],
        ["C. Tenaga kerja dan jasa", "Programmer IoT dan integrasi sistem", "1 paket", 8_000_000],
        ["C. Tenaga kerja dan jasa", "Desain teknis dan pengawasan lapangan", "1 paket", 5_000_000],
        ["D. Uji coba dan kalibrasi", "Uji fungsi sistem pengering (3 siklus)", "1 paket", 6_000_000],
        ["D. Uji coba dan kalibrasi", "Kalibrasi sensor dan instrumen", "1 paket", 3_000_000],
        ["D. Uji coba dan kalibrasi", "Uji mutu gabah dan beras", "1 paket", 4_000_000],
        ["E. Lain-lain", "Dokumentasi, publikasi, dan pelaporan", "1 paket", 4_000_000],
        ["E. Lain-lain", "Pelatihan operasi pengeringan dan IoT", "4 kali", 6_000_000],
        ["E. Lain-lain", "Pelatihan kemasan dan packing", "2 kali", 3_000_000],
        ["E. Lain-lain", "Pelatihan pemasaran dan pengelolaan", "2 kali", 3_000_000],
        ["E. Lain-lain", "Pemasaran online", "2 kali", 3_000_000],
        ["E. Lain-lain", "Pelatihan website dan e-market", "2 kali", 3_000_000],
        ["E. Lain-lain", "Survei", "4 kali", 10_000_000],
        ["E. Lain-lain", "Pelatihan", "12 kali", 18_000_000],
        ["E. Lain-lain", "Monitoring dan evaluasi", "4 kali", 10_000_000],
        ["E. Lain-lain", "Monitoring dan evaluasi pascaimplementasi", "1 paket", 6_000_000],
    ], columns=["Kelompok", "Komponen", "Volume", "Jumlah"])
    total_rab = rab["Jumlah"].sum()
    pos = [("Alat dan konstruksi", "#d19a38", ["A. Peralatan dan bahan utama", "B. Instalasi dan konstruksi"]),
           ("Jasa dan uji coba", "#58a6ff", ["C. Tenaga kerja dan jasa", "D. Uji coba dan kalibrasi"]),
           ("Pelatihan, survei, dan monev", "#3fb950", ["E. Lain-lain"])]
    nilai_pos = [(n, w, rab[rab["Kelompok"].isin(g)]["Jumlah"].sum()) for n, w, g in pos]

    sek("Rencana anggaran biaya", f"Total Rp {f1(total_rab, 0)} untuk 12 bulan pelaksanaan. "
        "Mitra: Pusat Organik PUSAKA BLORA dan PT Pertamina EP Cepu Field Cepu.")
    html('<div class="rab-bar">' + "".join(f'<div style="width:{v / total_rab * 100:.2f}%;background:{w}"></div>'
                                          for _, w, v in nilai_pos) + '</div>'
         + '<div class="rab-grid">' + "".join(
             f'<div class="rab-kartu" style="--c:{w}"><div class="n">{n}</div><div class="v">Rp {f1(v, 0)}</div>'
             f'<div class="p">{f1(v / total_rab * 100)} % dari total anggaran</div></div>' for n, w, v in nilai_pos)
         + '</div>')
    with st.expander("Lihat rincian 28 butir RAB"):
        isi = ""
        for kel, grup in rab.groupby("Kelompok", sort=False):
            isi += (f'<tr class="grup"><td colspan="2">{kel}</td><td></td>'
                    f'<td class="num">Rp {f1(grup["Jumlah"].sum(), 0)}</td></tr>')
            isi += "".join(f'<tr><td style="width:6%"></td><td>{r.Komponen}</td><td class="num">{r.Volume}</td>'
                           f'<td class="num">Rp {f1(r.Jumlah, 0)}</td></tr>' for r in grup.itertuples())
        isi += (f'<tr class="total"><td colspan="3">Total</td><td class="num">Rp {f1(total_rab, 0)}</td></tr>')
        html('<div class="spek-wrap"><table class="spek ringkas"><thead><tr><th style="width:6%"></th><th>Komponen</th>'
             '<th style="width:14%;text-align:right">Volume</th><th style="width:20%;text-align:right">Jumlah</th></tr>'
             f'</thead><tbody>{isi}</tbody></table></div>')

    sek("Sensor dan panel yang menampilkannya", "Tempat memantau setiap sensor di dasbor.")
    tabel([
        ("Suhu dan kelembapan (T&amp;RH) per rak", "Panel operasional: kabinet rak, grafik suhu dan RH"),
        ("Kadar air gabah (MC)", "Panel operasional: kinetika pengeringan"),
        ("Suhu ruang bakar", "Energi hibrida dan diagram alir"),
        ("Suhu dan efisiensi penukar panas", "Emisi dan kualitas udara, diagram alir"),
        ("Kualitas udara buang", "Emisi dan kualitas udara (CO dan partikulat)"),
        ("Kualitas udara masuk", "Emisi dan kualitas udara"),
        ("Monitoring energi PLTS dan baterai", "Energi hibrida dan diagram alir"),
    ], ("Sensor", "Ditampilkan di"), lebar_kiri="34%")

    sek("Asumsi model simulasi demo", "Angka simulasi. Akan diganti data pengukuran setelah uji lapangan.")
    tabel([
        ("Skala waktu", "Skala 4 menit demo = 24 jam proses (10 detik = 1 jam, 1 detik = 6 menit)"),
        ("Jumlah titik sensor rak", "3 zona (rak atas, tengah, bawah) untuk memantau keseragaman pengeringan"),
        ("Kinetika", "Model Lewis dengan KA setimbang Henderson termodifikasi (konstanta gabah). Laju bergantung pada suhu "
                     "dan aliran udara, dikalibrasi ke hasil uji lapangan (KA 27,72 % menjadi 14 % dalam 24 jam)"),
        ("Hasil kalibrasi", "Skenario standar: Rak Bawah ±17 jam, Rak Tengah ±20 jam, Rak Atas ±22 jam"),
        ("Kendali suhu", "Kendali PI pada daya tungku dengan setpoint bawaan 45 °C. Alarm menyala bila suhu rak di atas "
                         "50 °C, dan tungku otomatis dikunci bila blower mati"),
        ("Blower", f"2 unit DC dengan total {P_BLOWER_MAKS_W:.0f} W. Mode hemat 70 % aktif bila baterai di bawah {SOC_HEMAT:.0f} %"),
        ("Baterai", f"{BATERAI_KWH:.0f} kWh (LiFePO4 48 V 200 Ah), SOC awal {SOC_AWAL:.0f} %"),
        ("Tungku biomassa", f"Kalor maksimum {Q_TUNGKU_MAKS_KW:.0f} kW ke udara, nilai kalor batang padi {LHV_JERAMI:.0f} MJ/kg, "
                            f"efisiensi tungku dan penukar panas {EFISIENSI_TUNGKU_HE * 100:.0f} %"),
        ("Penukar panas", "Efektivitas 73-83 %, turun sedikit saat daya tungku tinggi"),
        ("Efek rumah kaca", "Kenaikan suhu udara hingga +12 °C pada iradiasi 1.000 W/m²"),
        ("Ambang alarm emisi", f"CO {AMBANG_CO:.0f} mg/Nm³, partikulat {AMBANG_PM:.0f} mg/Nm³, beda tekanan filter "
                               f"{AMBANG_DP_FILTER:.0f} Pa (setelan internal)"),
        ("Pembanding CO₂", "Panas biomassa dibanding pengering LPG (46 MJ/kg, efisiensi 85 %, 2,98 kg CO₂/kg), sedangkan "
                           "listrik PLTS dibanding jaringan (0,87 kg CO₂/kWh)"),
    ], ("Aspek", "Nilai yang dipakai"))


# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
html("""
<div style="text-align:center;color:#697184;font-size:12px;line-height:1.7;">
<b style="color:#9299a8;">SI-PADI: Pengering Padi Surya Terintegrasi IoT</b><br>
Kompetisi Inovasi Teknologi dan Energi, Program PFsains Pertamina Foundation 2026<br>
Ketua: Prof. Dr. Ir. Widayat, S.T., M.T., IPM., ASEAN Eng. (Universitas Diponegoro)<br>
Tim: Ir. Ali Mutakin, S.Kom. · Yusron Mahendra Diwiyanto, S.T. · Hasan Mustafa Widayat, S.T. · Dr. Norman Iskandar, S.T., M.T.<br>
Mitra: Pusat Organik PUSAKA BLORA · PT Pertamina EP Cepu Field Cepu
</div>
""")

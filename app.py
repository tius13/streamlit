import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurasi dasar halaman Streamlit
st.set_page_config(
    page_title="MONEY-TOR: Dashboard Penjualan UMKM",
    layout="wide"
)

# 1. LOAD DATA 
@st.cache_data
def load_data():
    df = pd.read_csv("main_data.csv")
    
    # Membersihkan nama kolom dari spasi yang tidak disengaja
    df.columns = df.columns.str.strip()
    
    # Memperbaiki konversi tanggal
    if 'tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['tanggal'])
    elif 'Tanggal' in df.columns:
        df['tanggal'] = pd.to_datetime(df['Tanggal'])
    
    # --- SISTEM PENGAMAN OTOMATIS KOLOM PROFIT ---
    if 'profit' not in df.columns:
        if 'Profit' in df.columns:
            df['profit'] = df['Profit']
        elif 'harga_modal' in df.columns and 'total_harga' in df.columns:
            # Hitung profit secara mandiri jika kolom hilang tapi harga modal ada
            df['profit'] = df['total_harga'] - (df['qty'] * df['harga_modal'])
        else:
            # Jika benar-benar tidak ada, buat estimasi profit 40% dari total harga agar dashboard tidak crash
            df['profit'] = df['total_harga'] * 0.4
            
    # Pastikan kolom tahun tersedia
    if 'tahun' not in df.columns and 'tanggal' in df.columns:
        df['tahun'] = df['tanggal'].dt.year

    df = df.sort_values('tanggal')
    return df

try:
    df_clean = load_data()
except FileNotFoundError:
    st.error("File 'main_data.csv' tidak ditemukan.")
    st.stop()

# 2. SIDEBAR PANEL FILTER (Actionable)
st.sidebar.header("Panel Kontrol Interaktif")

# Filter Berdasarkan Tahun
list_tahun = sorted(df_clean['tahun'].unique())
selected_years = st.sidebar.multiselect(
    "Pilih Tahun Analisis:", 
    options=list_tahun, 
    default=list_tahun
)

# Filter Berdasarkan Status Transaksi
if 'status_transaksi' in df_clean.columns:
    list_status = df_clean['status_transaksi'].unique()
    default_status = ["Berhasil"] if "Berhasil" in list_status else [list_status[0]]
else:
    list_status = ["Berhasil"]
    df_clean['status_transaksi'] = "Berhasil"
    default_status = ["Berhasil"]

selected_status = st.sidebar.multiselect(
    "Status Transaksi:", 
    options=list_status, 
    default=default_status
)

# Menerapkan filter ke dataset utama
df_filtered = df_clean[
    (df_clean['tahun'].isin(selected_years)) & 
    (df_clean['status_transaksi'].isin(selected_status))
].copy()

# Menyisipkan CSS kustom agar teks metric tidak terpotong ke bawah/titik-titik
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        white-space: normal !important;
        word-break: break-all !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. METRIK UTAMA OPERASIONAL 
st.title("Capstone Project: Dashboard Interaktif MONEY-TOR")
st.markdown("Aplikasi visualisasi data operasional untuk melacak performa transaksi finansial UMKM sepanjang tahun 2024 - 2026.")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    total_rev = df_filtered['total_harga'].sum() if not df_filtered.empty else 0
    st.metric(label="Total Pendapatan", value=f"Rp {total_rev:,.0f}")
with col2:
    total_profit = df_filtered['profit'].sum() if not df_filtered.empty else 0
    st.metric(label="Total Keuntungan (Profit)", value=f"Rp {total_profit:,.0f}")
with col3:
    total_trans = df_filtered['id_transaksi'].nunique() if not df_filtered.empty else 0
    st.metric(label="Total Transaksi Unik", value=f"{total_trans:,}")
with col4:
    total_items = df_filtered['qty'].sum() if not df_filtered.empty else 0
    st.metric(label="Total Kuantitas Terjual", value=f"{total_items:,}")

st.markdown("---")

# 4. VISUALISASI UTAMA 
if not df_filtered.empty:
    
    # Baris Pertama: Pertanyaan Bisnis 1 (Tahunan) & Pertanyaan Bisnis 2
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        st.subheader("Tren total pendapatan UMKM (2024 -2026)")
        trend_year = df_filtered.groupby('tahun')['total_harga'].sum().reset_index()
        trend_year['tahun'] = trend_year['tahun'].astype(str)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(
            data=trend_year, 
            x='tahun', 
            y='total_harga', 
            marker='o', 
            color='#1f77b4', 
            linewidth=3, 
            markersize=8,
            ax=ax
        )
        
        for i, row in trend_year.iterrows():
            ax.annotate(f"Rp {row['total_harga']:,.0f}", 
                        (row['tahun'], row['total_harga']),
                        textcoords="offset points", 
                        xytext=(0,10), 
                        ha='center', 
                        fontsize=9, 
                        fontweight='bold')
            
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Total Pendapatan (Rp)")
        ax.set_ylim(trend_year['total_harga'].min() * 0.8, trend_year['total_harga'].max() * 1.2)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        st.pyplot(fig)
        
    with row1_col2:
        st.subheader("Kategori produk dengan pendapatan tertinggi / pendapatan tertinggi berdasarkan kategori produk")
        category_revenue = df_filtered.groupby('kategori')['total_harga'].sum().sort_values(ascending=False).reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=category_revenue, x='total_harga', y='kategori', palette='Blues_r', ax=ax)
        ax.set_xlabel("Total Pendapatan (Rp)")
        ax.set_ylabel("Kategori Produk")
        st.pyplot(fig)

    st.markdown("---")
    
    # Baris Kedua: Pertanyaan Bisnis 3 & 4
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.subheader("Pengaruh Event promosi")
        event_revenue = df_filtered.groupby('event')['total_harga'].sum().sort_values(ascending=False).reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=event_revenue, x='total_harga', y='event', palette='viridis', ax=ax)
        ax.set_xlabel("Total Nilai Transaksi (Rp)")
        ax.set_ylabel("Event Promosi")
        st.pyplot(fig)
        
    with row2_col2:
        st.subheader("Frekuensi metode pembayaran")
        payment_distribution = df_filtered['metode_pembayaran'].value_counts().reset_index()
        payment_distribution.columns = ['metode_pembayaran', 'jumlah_penggunaan']
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.pie(
            payment_distribution['jumlah_penggunaan'], 
            labels=payment_distribution['metode_pembayaran'], 
            autopct='%1.1f%%', 
            startangle=140,
            colors=['#2ca02c', '#ff7f0e', '#d62728']
        )
        ax.axis('equal') 
        st.pyplot(fig)

else:
    st.warning("Tidak ada data operasional yang sesuai dengan kombinasi filter Anda saat ini.")

# 5. DATASET EXPLORER 
st.markdown("---")
st.subheader("Cuplikan Sampel Data Terfilter")
st.dataframe(df_filtered.head(100), use_container_width=True)

st.caption("Dashboard MONEY-TOR | Dikembangkan Menggunakan Streamlit.")

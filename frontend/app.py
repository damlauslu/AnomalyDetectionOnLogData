import streamlit as st
import requests
from data_loader import load_data
from dashboard import show_general_dashboard
from api_utils import post_preprocess_api
from visualization import (
    plot_access_duration_histogram,
    plot_user_access_bar,
    plot_time_series
)
import jwt
import time


API_URL = "http://localhost:5000"  # Flask API URL

st.set_page_config(page_title="Anomali Tespit Arayüzü", layout="wide")
st.title("📊 Anomali Tespit Uygulaması")

# Session kontrolü
if "token" not in st.session_state:
    st.session_state.token = None

# Token çözümlemesi
user_info = None
if st.session_state.token:
    try:
        user_info = jwt.decode(st.session_state.token, options={"verify_signature": False})
        st.success(f"Giriş başarılı! Hoş geldin {user_info['username']} ({user_info['role']})")
    except Exception:
        st.session_state.token = None
        st.warning("Geçersiz token, tekrar giriş yapın.")

# Giriş ekranı
if not st.session_state.token:
    with st.form("login_form"):
        st.subheader("🔐 Giriş Yap")
        username = st.text_input("Kullanıcı adı")
        password = st.text_input("Şifre", type="password")
        submitted = st.form_submit_button("Giriş")

        if submitted:
            res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state.token = res.json()["token"]
                st.success("Giriş başarılı, yönlendiriliyorsunuz...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Giriş başarısız. Lütfen bilgileri kontrol edin.")

# Giriş başarılıysa arayüz
elif user_info:

    role = user_info["role"]

    st.sidebar.subheader("👤 Oturum")
    if st.sidebar.button("🚪 Çıkış Yap"):
        st.session_state.token = None
        st.rerun()

    uploaded_file = st.file_uploader("Veri dosyasını yükleyin (.csv, .xlsx):", type=["csv", "xlsx"])
    if uploaded_file:
        df, error = load_data(uploaded_file)
        if error:
            st.error(error)
        else:
            st.success("Veri başarıyla yüklendi ✅")
            show_general_dashboard(df)
            st.markdown("---")

            uploaded_file.seek(0)

            extension = uploaded_file.name.split(".")[-1]
            with open(f"temp_uploaded.{extension}", "wb") as f:
                f.write(uploaded_file.read())


if role in ["admin", "analyst"]:
    if st.button("🚀 Anomali Tespitini Başlat"):
        if uploaded_file:
            with st.spinner("Model çalıştırılıyor..."):
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                res = requests.post(
                    f"{API_URL}/run-detection",
                    files={"file": uploaded_file},
                    headers=headers
                )
            if res.status_code == 200:
                result = res.json()
                st.success("✅ Anormal kullanıcılar başarıyla tespit edildi.")
                st.json(result['abnormal_users'])
            else:
                st.error(f"❌ Hata oluştu: {res.text}")


            st.subheader("🧾 Veri Önizleme")
            st.dataframe(df.head())
    else:
        st.info("Lütfen bir veri dosyası yükleyin.")
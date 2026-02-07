import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import easyocr
import numpy as np
from PIL import Image

# --- CONFIG & MODERN THEME ---
st.set_page_config(page_title="RTE Dashboard", layout="wide")

# CSS สำหรับธีมขาว-แดง-ดำ ให้ดูหรูหรา
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    div[data-testid="stMetric"] { background-color: #fcfcfc; border: 1px solid #eeeeee; border-radius: 10px; padding: 15px; border-top: 4px solid #cc0000; }
    div[data-testid="stSidebar"] { background-color: #000000; }
    section[data-testid="stSidebar"] .stRadio label { color: white !important; }
    h1, h2, h3 { color: #111111; }
    </style>
    """, unsafe_allow_html=True)

TARGET_REVENUE = 170000.0

# --- MASTER DATA ---
CATEGORY_MAP = {
    "203081": "ทานเล่น", "250561": "ทานเล่น", "274583": "ทานเล่น", "299207": "ทานเล่น",
    "381059": "ทานเล่น", "395441": "ทานเล่น", "614329": "ทานเล่น", "619903": "ทานเล่น",
    "648962": "ทานเล่น", "779278": "ทานเล่น", "782617": "ทานเล่น", "956994": "ทานเล่น",
    "231259": "พร้อมทาน", "302490": "พร้อมทาน", "322224": "พร้อมทาน", "344174": "พร้อมทาน",
    "364882": "พร้อมทาน", "380450": "พร้อมทาน", "621822": "พร้อมทาน", "654830": "พร้อมทาน",
    "695884": "พร้อมทาน", "724276": "พร้อมทาน", "781110": "พร้อมทาน", "951651": "พร้อมทาน",
    "250271": "พร้อมทาน", "273023": "พร้อมทาน", "967970": "พร้อมทาน"
}

PRODUCT_NAMES = {
    "203081": "ฮ็อทด็อก", "250561": "ขนมจีบหมู ชุดใหญ่", "274583": "ชุดรวมของทอด",
    "299207": "ไก่ป๊อปชุดใหญ่", "381059": "นักเก็ตไก่คลาสสิค", "395441": "ฮะเก๋าชุดใหญ่",
    "614329": "เกี๊ยวซ่าหมูกุยช่าย ชุดใหญ่", "619903": "ปีกไก่บนคลุกซอส",
    "648962": "ฮะเก๋าโปรโมชั่น", "779278": "ไก่ป๊อป", "782617": "เกี๊ยวซ่าหมูชุดใหญ่",
    "956994": "นักเก็ตชุดใหญ่", "231259": "เนื้อเป็ดย่างเครื่องเทศ", 
    "302490": "บะหมี่หมูแดงใหญ่", "322224": "ยำหมูกรอบ", "344174": "ขาหมูเยอรมัน", 
    "364882": "หมูแดง", "380450": "บะหมี่เป็ดย่างใหญ่", "621822": "อาหารพร้อมทาน 99 บาท", 
    "654830": "เป็ดพะโล้พร้อมไส้", "695884": "หมูกรอบ แพ็คใหญ่", 
    "724276": "ขาหมูพะโล้ (เลาะเนื้อ)", "781110": "บะหมี่เป็ดพะโล้ใหญ่", 
    "951651": "กุ้งต้ม", "250271": "บะหมี่เป็ดย่าง", 
    "273023": "บะหมี่หมูแดงสไตล์ฮ่องกง", "967970": "บะหมี่เนื้อเป็ดพะโล้"
}

@st.cache_resource
def get_reader():
    return easyocr.Reader(['th', 'en'])

reader = get_reader()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>RTE MANAGEMENT</h2>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["🏢 Overview", "🍖 Snack Category", "🍲 Meal Category"])
    st.divider()
    uploaded_file = st.file_uploader("Upload Summary Image", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    with st.spinner('🚀 AI Is Extracting Data...'):
        result = reader.readtext(img_np)
        full_text = [res[1] for res in result]
        
        extracted = {}
        for i, text in enumerate(full_text):
            code = text.replace(" ", "").strip()
            if code in CATEGORY_MAP:
                try:
                    q = float(full_text[i+2].replace(",", ""))
                    a = float(full_text[i+3].replace(",", ""))
                    extracted[code] = {"q": q, "a": a}
                except: continue

        # กระจายยอด 99 บาท (621822)
        if "621822" in extracted:
            p99 = extracted.pop("621822")
            for c, r in {"231259": 0.5, "654830": 0.3, "724276": 0.2}.items():
                if c not in extracted: extracted[c] = {"q": 0, "a": 0}
                extracted[c]["q"] += p99["q"] * r
                extracted[c]["a"] += p99["a"] * r

        # สร้าง DataFrame (ใช้ชื่อคอลัมน์ภาษาอังกฤษเพื่อความชัวร์)
        data = []
        for c, v in extracted.items():
            data.append({
                "Category": CATEGORY_MAP[c],
                "ArtNo": c,
                "Name": PRODUCT_NAMES[c],
                "Qty": v["q"],
                "Amt_Net": v["a"],
                "Amt_Vat": round(v["a"] * 1.07, 2)
            })
        
        df = pd.DataFrame(data)

    if not df.empty:
        if page == "🏢 Overview":
            st.title("📊 Sales Summary Overview")
            
            # --- Gauge Achievement ---
            total_sales = df["Amt_Vat"].sum()
            achieve = (total_sales / TARGET_REVENUE) * 100
            
            c1, c2 = st.columns([2, 1])
            with c1:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = total_sales,
                    title = {'text': "Revenue Achievement vs Target"},
                    gauge = {'axis': {'range': [None, TARGET_REVENUE]},
                             'bar': {'color': "#cc0000"},
                             'steps': [{'range': [0, TARGET_REVENUE], 'color': "#f2f2f2"}]}))
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.metric("Achievement (%)", f"{achieve:.2f}%")
                st.metric("Total Sales (Inc. VAT)", f"{total_sales:,.2f}")
                st.metric("Gap to Target", f"{max(0, TARGET_REVENUE - total_sales):,.2f}")

            # --- 3 Items ยอดตก ---
            st.subheader("⚠️ 3 รายการยอดขายน้อยที่สุด (Low Performers)")
            low_3 = df.sort_values("Qty").head(3)
            cols = st.columns(3)
            for i, row in enumerate(low_3.itertuples()):
                cols[i].warning(f"**{row.Name}**\nQty: {row.Qty} | Total: {row.Amt_Vat:,.2f}")

            # --- Full Ranking Table ---
            st.subheader("🏆 รายการสินค้าทั้งหมด (เรียงตาม Qty)")
            st.table(df.sort_values("Qty", ascending=False).style.format({"Amt_Net": "{:,.2f}", "Amt_Vat": "{:,.2f}"}))

        else:
            # --- หน้าแยกหมวดหมู่ ---
            cat_name = "ทานเล่น" if "Snack" in page else "พร้อมทาน"
            st.title(f"📍 หมวด{cat_name}")
            sub_df = df[df["Category"] == cat_name].sort_values("Qty", ascending=False)
            
            if not sub_df.empty:
                st.metric(f"ยอดรวมสุทธิ {cat_name}", f"{sub_df['Amt_Vat'].sum():,.2f}")
                fig_bar = px.bar(sub_df, x="Name", y="Amt_Vat", text="Qty", color_discrete_sequence=['#333333'])
                st.plotly_chart(fig_bar, use_container_width=True)
                st.table(sub_df.style.format({"Amt_Net": "{:,.2f}", "Amt_Vat": "{:,.2f}"}))
            else:
                st.warning("ไม่มีข้อมูลในหมวดนี้จากรูปที่อัปโหลด")
else:
    st.info("👈 กรุณาอัปโหลดรูปภาพใบสรุปยอดขายที่เมนูด้านซ้าย")

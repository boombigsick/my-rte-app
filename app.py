import streamlit as st
import pandas as pd
import plotly.express as px
import easyocr
import numpy as np
from PIL import Image

st.set_page_config(page_title="RTE Sales Pro", layout="wide")
st.title("📊 RTE Auto-Sales Analyst")

# ข้อมูลเมนูของคุณ
TARGET_ITEMS = {
    "203081": "ฮ็อทด็อก", "250561": "ขนมจีบหมู ชุดใหญ่", "274583": "ชุดรวมของทอด",
    "299207": "ไก่ป๊อปชุดใหญ่", "381059": "นักเก็ตไก่คลาสสิค", "395441": "ฮะเก๋าชุดใหญ่",
    "614329": "เกี๊ยวซ่าหมูกุยช่าย ชุดใหญ่", "619903": "ปีกไก่บนคลุกซอส",
    "648962": "ฮะเก๋าโปรโมชั่น", "779278": "ไก่ป๊อป", "782617": "เกี๊ยวซ่าหมูชุดใหญ่",
    "956994": "นักเก็ตชุดใหญ่"
}

# โหลด Reader ครั้งเดียวเพื่อประหยัดความจำ
@st.cache_resource
def get_reader():
    return easyocr.Reader(['th', 'en'])

reader = get_reader()

uploaded_file = st.file_uploader("📷 อัปโหลดรูปยอดขาย (ระบุวันที่ในชื่อไฟล์ได้)", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="รูปภาพที่นำเข้า", width=400)
    
    with st.spinner('AI กำลังวิเคราะห์และเรียงลำดับสินค้า...'):
        img_np = np.array(image)
        result = reader.readtext(img_np)
        
        extracted_data = []
        full_text_list = [res[1] for res in result]
        
        # ค้นหาข้อมูลตามรหัสสินค้า
        for i, text in enumerate(full_text_list):
            clean_code = text.replace(" ", "").strip()
            if clean_code in TARGET_ITEMS:
                try:
                    # พยายามหาตัวเลข Qty และ Amount ในบริเวณใกล้เคียง
                    qty = float(full_text_list[i+2].replace(",", ""))
                    amt = float(full_text_list[i+3].replace(",", ""))
                    extracted_data.append({
                        "รหัสสินค้า": clean_code,
                        "ชื่อสินค้า": TARGET_ITEMS[clean_code],
                        "Qty Sum": qty,
                        "Amount (+Vat 7%)": round(amt * 1.07, 2)
                    })
                except: continue

        if extracted_data:
            df = pd.DataFrame(extracted_data)
            # เรียงลำดับจาก Qty มากไปน้อย
            df = df.sort_values(by="Qty Sum", ascending=False).reset_index(drop=True)
            
            # คำนวณ % ส่วนแบ่งยอดขาย
            total_sales = df["Amount (+Vat 7%)"].sum()
            df["ส่วนแบ่งยอดขาย (%)"] = ((df["Amount (+Vat 7%)"] / total_sales) * 100).round(2)

            # --- แสดงผลกราฟเส้น ---
            st.subheader("📈 แนวโน้มยอดขาย (Trend)")
            fig = px.line(df, x="ชื่อสินค้า", y="Amount (+Vat 7%)", markers=True, 
                          text="Amount (+Vat 7%)", title="Sales Value Chart")
            st.plotly_chart(fig, use_container_width=True)

            # --- แสดงตารางและ Mark Top 3 ---
            st.subheader("🏆 อันดับสินค้าขายดี (Top Qty)")
            
            def highlight_top3(row):
                # ไฮไลท์สีตามอันดับ
                if row.name == 0: color = '#FFD700' # ทอง
                elif row.name == 1: color = '#C0C0C0' # เงิน
                elif row.name == 2: color = '#CD7F32' # ทองแดง
                else: color = ''
                
                return [f'background-color: {color}; color: black; font-weight: bold' if color else '' for _ in row]

            st.dataframe(df.style.apply(highlight_top3, axis=1), use_container_width=True)
            
            # สรุปผล
            st.info(f"💡 สินค้าอันดับ 1 ({df['ชื่อสินค้า'][0]}) ครองสัดส่วนยอดขายถึง {df['ส่วนแบ่งยอดขาย (%)'][0]}% ของยอดรวมทั้งหมด")
        else:
            st.error("❌ ไม่พบรหัสสินค้าในรูปภาพ กรุณาตรวจสอบว่ารูปภาพชัดเจน")

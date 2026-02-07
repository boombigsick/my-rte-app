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

@st.cache_resource
def get_reader():
    return easyocr.Reader(['th', 'en'])

reader = get_reader()

uploaded_file = st.file_uploader("📷 อัปโหลดรูปยอดขาย", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="รูปภาพที่นำเข้า", width=400)
    
    with st.spinner('AI กำลังคำนวณยอดรวมทั้ง 2 แบบ...'):
        img_np = np.array(image)
        result = reader.readtext(img_np)
        
        extracted_data = []
        full_text_list = [res[1] for res in result]
        
        for i, text in enumerate(full_text_list):
            clean_code = text.replace(" ", "").strip()
            if clean_code in TARGET_ITEMS:
                try:
                    qty = float(full_text_list[i+2].replace(",", ""))
                    amt_before_vat = float(full_text_list[i+3].replace(",", ""))
                    extracted_data.append({
                        "รหัสสินค้า": clean_code,
                        "ชื่อสินค้า": TARGET_ITEMS[clean_code],
                        "Qty Sum": qty,
                        "ยอดก่อน VAT": round(amt_before_vat, 2),
                        "ยอดสุทธิ (+Vat 7%)": round(amt_before_vat * 1.07, 2)
                    })
                except: continue

        if extracted_data:
            df = pd.DataFrame(extracted_data)
            df = df.sort_values(by="Qty Sum", ascending=False).reset_index(drop=True)
            
            # คำนวณยอดรวมทั้งหมด
            total_qty = df["Qty Sum"].sum()
            total_before_vat = df["ยอดก่อน VAT"].sum()
            total_after_vat = df["ยอดสุทธิ (+Vat 7%)"].sum()
            
            # คำนวณ % ส่วนแบ่ง (อิงจากยอดสุทธิ)
            df["ส่วนแบ่ง (%)"] = ((df["ยอดสุทธิ (+Vat 7%)"] / total_after_vat) * 100).round(2)

            # --- สร้างแถวสรุปยอดรวม (Grand Total) ---
            total_row = pd.DataFrame([{
                "รหัสสินค้า": "TOTAL",
                "ชื่อสินค้า": "ยอดรวมทั้งหมด",
                "Qty Sum": total_qty,
                "ยอดก่อน VAT": total_before_vat,
                "ยอดสุทธิ (+Vat 7%)": total_after_vat,
                "ส่วนแบ่ง (%)": 100.0
            }])
            
            df_with_total = pd.concat([df, total_row], ignore_index=True)

            # --- กราฟเส้นแนวโน้มยอดขาย ---
            st.subheader("📈 กราฟแนวโน้มยอดขายสุทธิ")
            fig = px.line(df, x="ชื่อสินค้า", y="ยอดสุทธิ (+Vat 7%)", markers=True, 
                          text="ยอดสุทธิ (+Vat 7%)")
            st.plotly_chart(fig, use_container_width=True)

            # --- ตารางสรุปผล ---
            st.subheader("🏆 รายงานสรุปยอดขาย (เรียงตาม Qty)")
            
            def highlight_rows(row):
                if row["รหัสสินค้า"] == "TOTAL":
                    return ['background-color: #2E4053; color: white; font-weight: bold; border-top: 2px solid white'] * len(row)
                elif row.name == 0: color = '#FFD700' # Gold
                elif row.name == 1: color = '#C0C0C0' # Silver
                elif row.name == 2: color = '#CD7F32' # Bronze
                else: color = ''
                return [f'background-color: {color}; color: black; font-weight: bold' if color else '' for _ in row]

            st.table(df_with_total.style.apply(highlight_rows, axis=1).format({
                "ยอดก่อน VAT": "{:,.2f}",
                "ยอดสุทธิ (+Vat 7%)": "{:,.2f}",
                "ส่วนแบ่ง (%)": "{}%"
            }))
            
            # --- กล่องสรุป 2 Total ---
            col1, col2 = st.columns(2)
            col1.metric("ยอดรวมก่อน VAT", f"{total_before_vat:,.2f} บาท")
            col2.metric("ยอดรวมสุทธิ (+VAT 7%)", f"{total_after_vat:,.2f} บาท", delta=f"VAT 7%: {total_after_vat-total_before_vat:,.2f}")
            
        else:
            st.error("❌ ไม่พบข้อมูลในรูปภาพ")

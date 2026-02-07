import streamlit as st
import pandas as pd
import plotly.express as px
import pytesseract
from PIL import Image
import re

# ตั้งค่าหน้าแอป
st.set_page_config(page_title="RTE Super Analyst", layout="wide")
st.title("🚀 RTE Auto-Analysis Dashboard")

# ข้อมูลเมนูที่กำหนด
TARGET_ITEMS = {
    "203081": "ฮ็อทด็อก", "250561": "ขนมจีบหมู ชุดใหญ่", "274583": "ชุดรวมของทอด",
    "299207": "ไก่ป๊อปชุดใหญ่", "381059": "นักเก็ตไก่คลาสสิค", "395441": "ฮะเก๋าชุดใหญ่",
    "614329": "เกี๊ยวซ่าหมูกุยช่าย ชุดใหญ่", "619903": "ปีกไก่บนคลุกซอส",
    "648962": "ฮะเก๋าโปรโมชั่น", "779278": "ไก่ป๊อป", "782617": "เกี๊ยวซ่าหมูชุดใหญ่",
    "956994": "นักเก็ตชุดใหญ่"
}

uploaded_file = st.file_uploader("📷 อัปโหลดรูปภาพยอดขาย", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="รูปภาพที่นำเข้า", width=400)
    
    with st.spinner('กำลังใช้ AI สแกนข้อมูล...'):
        # สแกนข้อความจากภาพ
        text_data = pytesseract.image_to_string(img, lang='eng+tha')
        lines = text_data.split('\n')
        
        final_list = []
        for line in lines:
            parts = line.split()
            for art_no, name in TARGET_ITEMS.items():
                if art_no in line:
                    # ใช้ Regex ดึงตัวเลข Qty และ Amount ที่อยู่ท้ายบรรทัด
                    numbers = re.findall(r"(\d+\.?\d*)", line.replace(",", ""))
                    if len(numbers) >= 3:
                        qty = float(numbers[-2])
                        amt = float(numbers[-1])
                        final_list.append({
                            "รหัสสินค้า": art_no,
                            "ชื่อสินค้า": name,
                            "Qty Sum": qty,
                            "Amount (+Vat 7%)": round(amt * 1.07, 2)
                        })

        if final_list:
            df = pd.DataFrame(final_list)
            # เรียงลำดับขายดีสุด (Qty) อยู่บนสุด
            df = df.sort_values(by="Qty Sum", ascending=False).reset_index(drop=True)
            
            # คำนวณ % ส่วนแบ่งยอดขาย
            total_amt = df["Amount (+Vat 7%)"].sum()
            df["สัดส่วนยอดขาย (%)"] = ((df["Amount (+Vat 7%)"] / total_amt) * 100).round(2)

            # --- ส่วนแสดงผล UX/UI ---
            
            # 1. กราฟเส้นภาพรวม
            st.subheader("📈 แนวโน้มยอดขายแต่ละรายการ")
            fig = px.line(df, x="ชื่อสินค้า", y="Amount (+Vat 7%)", markers=True, 
                          text="Amount (+Vat 7%)", title="Sales Trend (Inc. VAT)")
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)

            # 2. ตารางอันดับสินค้า
            st.subheader("🏆 อันดับสินค้าขายดี (Sorted by Qty)")
            
            # ฟังก์ชันไฮไลท์ Top 3 เป็นสีทอง
            def style_top3(row):
                if row.name < 3:
                    return ['background-color: #f1c40f; color: black; font-weight: bold'] * len(row)
                return [''] * len(row)

            st.table(df.style.apply(style_top3, axis=1))
            
            # สรุป Insight
            top3_share = df["สัดส่วนยอดขาย (%)"].head(3).sum()
            st.success(f"🔥 วิเคราะห์สำเร็จ: สินค้า Top 3 ครองส่วนแบ่งยอดขายถึง {top3_share}% ของทั้งหมด!")
            
        else:
            st.warning("⚠️ ไม่พบรหัสสินค้าที่กำหนดในรูปภาพ โปรดตรวจสอบว่ารูปชัดเจนและเห็นรหัสสินค้า (Art no)")

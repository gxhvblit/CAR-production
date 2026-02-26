import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from gspread_dataframe import set_with_dataframe

# === ฟังก์ชันเชื่อมต่อ Google Sheets แบบ Online ===
def connect_gsheet():
    # ดึงค่า JSON Key จากระบบ Secrets ของ Streamlit Cloud
    creds_info = st.secrets["gcp_service_account"]
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(creds)
    
    # ลิงก์ Sheets ล่าสุดที่คุณให้มา
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1uzqqb28dE2eOkwIt5eNh1nOq1DQ6DiNW9L0h7Ptve9Y/edit#gid=0"
    spreadsheet = gc.open_by_url(SHEET_URL)
    return spreadsheet.get_worksheet(0) # ลงที่ Sheet1

# === ฟังก์ชัน Logic การดึงข้อมูล ===
def get_val(df, row, cols):
    if isinstance(cols, list):
        return sum(df.loc[row, col] for col in cols)
    return df.loc[row, cols]

# === หน้าตาแอปบนเว็บ ===
st.set_page_config(page_title="Production Routine Online", layout="wide")
st.title("🌐 ระบบจัดการข้อมูลการผลิตรถยนต์ (Online Version)")

uploaded_files = st.file_uploader("📂 อัปโหลดไฟล์ Excel ของคุณที่นี่", type=["xls", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    records = []
    row_idx = 21 # แถวที่ 21 ตาม Logic ของคุณ
    
    for file in uploaded_files:
        try:
            df = pd.read_excel(file, sheet_name="Production")
            # Logic ดึงปี/เดือนจากชื่อไฟล์ (Production_MMYYYY...)
            fname = file.name.split('_')[1]
            m_code = fname[:2]
            y_code = fname[4:6]
            
            month_map = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
                         "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
            
            records.append({
                "Month": month_map.get(m_code, "N/A"),
                "Year": 2500 + int(y_code),
                "Passenger": get_val(df, row_idx, 'Unnamed: 17'),
                "Pickup": get_val(df, row_idx, ['Unnamed: 24', 'Unnamed: 25', 'Unnamed: 26']),
                "Commercial": get_val(df, row_idx, ['Unnamed: 19', 'Unnamed: 27', 'Unnamed: 28', 'Unnamed: 29']),
                "Total": get_val(df, row_idx, 'Unnamed: 4')
            })
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")

    if records:
        df_summary = pd.DataFrame(records)
        # จัดเรียงลำดับคอลัมน์
        df_summary = df_summary[["Month", "Year", "Passenger", "Pickup", "Commercial", "Total"]].round(2)
        
        st.subheader("📋 ตรวจสอบข้อมูลก่อนบันทึก")
        edited_df = st.data_editor(df_summary, num_rows="dynamic", use_container_width=True)

        if st.button("📤 บันทึกไปที่ Google Sheets ทันที"):
            try:
                with st.spinner('กำลังเชื่อมต่อระบบ...'):
                    worksheet = connect_gsheet()
                    set_with_dataframe(worksheet, edited_df)
                    st.success("บันทึกข้อมูลออนไลน์สำเร็จ! ✅")
                    st.balloons()
            except Exception as e:
                st.error(f"การบันทึกล้มเหลว: {e}")
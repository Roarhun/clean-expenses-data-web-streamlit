import streamlit as st
import pandas as pd
import io


def clean_data(df, month, year, fiscal_year):
    
    # ลบแถวสุดท้าย(ผลรวม)
    df = df[:-1]

    # แปลงชนิดข้อมูล - float
    columns_to_float = ['งบประมาณตั้งต้น', 'เงินงวด', 'โอน', 'เพิ่ม/ลด', 
                        'งบเพิ่มเติมระหว่างปี', 'เงินงวดทั้งหมด', 
                        'ขอโอน', 'ใบจอง', 'PO', 'กันเงินยกไป']
    df[columns_to_float] = df[columns_to_float].astype(float)
    
    # แปลงชนิดข้อมูล - string
    columns_to_str = ['Fund', 'Funds Center']
    df[columns_to_str] = df[columns_to_str].astype(int)
    df[columns_to_str] = df[columns_to_str].astype(str)

    # ลบแถวว่าง
    df = df.dropna()

    # แยกประเภทงบ
    def determine_type(item):
        if item.startswith('1000010001'):  # เงินเดือน
            return 'งบบุคลากร'
        elif item.startswith('2000010001'):  # งบดำเนินงาน
            return 'งบดำเนินงาน'
        elif item.startswith('2000020001'):  # งบดำเนินงาน
            return 'งบดำเนินงาน'
        elif item.startswith('3'):
            return 'งบลงทุน'
        elif item.startswith('400'):
            return 'งบเงินอุดหนุน'
        elif item.startswith('600'):
            return 'งบกลาง'
        elif item.startswith('500'):
            return 'งบรายจ่ายอื่น'
        else:
            return 'unknown'

    # Apply the type determination function
    df['Commitment Item'] = df['Commitment Item'].astype(str)
    df['Commitment Item Type'] = df['Commitment Item'].apply(determine_type)

    # Add month and year columns
    df['month'] = month
    df['year'] = year

    # Ensure valid data in 'Functional Area'
    df['Functional Area'] = df['Functional Area'].astype(str).fillna('')

    # Filter rows based on conditions
    fiscal_year_last_two = str(fiscal_year)[-2:]
    df_filtered = df[~df['Commitment Item'].str.startswith(('Z', '9000'))]
    df_filtered = df_filtered[df_filtered['Functional Area'].str[:2] == fiscal_year_last_two]
    df = df_filtered


    #process for main data file
    def process_special_data(df):
        #ตั้งตัวแปรเก็บข้อมูลแถวที่ขึ้นต้นด้วย 3xx1 3xx2
        special_rows1 = df[df['Commitment Item'].str.contains(r'^3..1')]
        special_rows2 = df[df['Commitment Item'].str.contains(r'^3..2')]
        #dataframe
        special_rows1=pd.DataFrame(special_rows1)
        special_rows2=pd.DataFrame(special_rows2)

        #สร้างแถวใหม่ที่จะเก็บข้อมูลของครุภัณฑ์ที่ทำการรวมแล้ว ในตัวแปร special_item
        special_item1 = pd.DataFrame({
            'Fund': [2010000000],
            'Fund Name': ['เงินรายได้'],
            'Functional Area': [f"{str(fiscal_year)[2]}" + f"{str(fiscal_year)[3]}" + '02001'],
            'Programme': ['แผนงานจัดการศึกษาอุดมศึกษา'],
            'Project/Output': ['งานสนับสนุนการจัดการศึกษา'],
            'Funds Center': ['1100000000'],
            'Funds Center Name': ['สำนักคอมพิวเตอร์'],
            'Commitment Item': ['ค่าครุภัณฑ์'],
            'Commitment Item Name': ['ค่าครุภัณฑ์'],
            **{col: special_rows1[col].sum() for col in special_rows1.columns[9:25]},
            'month': [month], 'year': [year],
            'Commitment Item Type': ['งบลงทุน']
        }, index=[0])

        special_item2 = pd.DataFrame({
            'Fund': [2010000000],
            'Fund Name': ['เงินรายได้'],
            'Functional Area': [f"{str(fiscal_year)[2]}" + f"{str(fiscal_year)[3]}" + '02001'],
            'Programme': ['แผนงานจัดการศึกษาอุดมศึกษา'],
            'Project/Output': ['งานสนับสนุนการจัดการศึกษา'],
            'Funds Center': ['1100000000'],
            'Funds Center Name': ['สำนักคอมพิวเตอร์'],
            'Commitment Item': ['ค่าสิ่งก่อสร้าง'],
            'Commitment Item Name': ['ค่าสิ่งก่อสร้าง'],
            **{col: special_rows2[col].sum() for col in special_rows2.columns[9:25]},
            'month': [month], 'year': [year],
            'Commitment Item Type': ['งบลงทุน']
        }, index=[0])


        #ไม่มี special
        df = df[~df['Commitment Item'].str.contains(r'^3..1')]
        df = df[~df['Commitment Item'].str.contains(r'^3..2')]

        #นำ dataframe ที่ไม่มีรายการครุภัณฑ์และสิ่งก่อสร้าง มารวมกับแถวที่รวมเป็นหมวดไว้แล้ว
        df = pd.concat([df, special_item1,special_item2], ignore_index=True)
        # return dataframe
        return df
    
    #process for item data
    def get_item_data(df):
    #เก็บข้อมูลที่เป็นรายการครุภัณฑ์
        item_rows_data = df[df['Commitment Item'].str.startswith('3')]
        item_rows_data = pd.DataFrame(item_rows_data)
        return item_rows_data
    

    # bring filtered df use function
    itemData = get_item_data(df)
    itemData['status'] = ""
    itemData['amount'] = itemData['ขอโอน'] + itemData['ใบจอง'] + itemData['PR'] + itemData['PO'] + itemData['ตั้งหนี้']
    mainData = process_special_data(df)
    # Return cleaned DataFrame
    return (itemData, mainData)

################################################################
def main():
    st.title("โปรแกรมทำความสะอาดข้อมูลงบประมาณ รายจ่าย")

    # Define month options
    month_options = {
        'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04', 
        'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08', 
        'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
    }

    # User inputs for month and year
    selected_month_abbr = st.selectbox("เลือกเดือน:", list(month_options.keys()))
    year = st.number_input("กรอกปี (พ.ศ.):", min_value=0, max_value=10000000000, step=1)
    fiscal_year = st.number_input("กรอกปีงบประมาณ (พ.ศ.):", min_value=0, max_value=10000000000, step=1)
    # Convert month abbreviation to numerical value
    month = month_options[selected_month_abbr]



    # File uploader for Excel files
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if selected_month_abbr and year and fiscal_year and uploaded_file is not None:
        # Read the uploaded Excel file
        df = pd.read_excel(uploaded_file, engine='openpyxl')

        st.write("ข้อมูลดิบ:")
        st.dataframe(df)

        # Clean the data and retrieve itemData and mainData
        itemData, mainData = clean_data(df, month, year, fiscal_year)

        st.write("ข้อมูลรายจ่าย:")
        st.dataframe(mainData)
        
        st.write("ข้อมูลรายการครุภัณฑ์ / สิ่งก่อสร้าง:")
        st.dataframe(itemData)

        

        # Create Excel files for both itemData and mainData
        main_output = io.BytesIO()
        item_output = io.BytesIO()
        
        with pd.ExcelWriter(main_output, engine='openpyxl') as writer:
            mainData.to_excel(writer, index=False, sheet_name='Main Data')
        main_output.seek(0)

        with pd.ExcelWriter(item_output, engine='openpyxl') as writer:
            itemData.to_excel(writer, index=False, sheet_name='Item Data')
        item_output.seek(0)

    

        # Buttons to download the itemData and mainData as separate Excel files
        st.download_button(
            label="ดาวน์โหลดไฟล์รายจ่าย",
            data=main_output,
            file_name=f"รายจ่าย_{month}_{year}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        st.download_button(
            label="ดาวน์โหลดไฟล์รายการครุภัณฑ์และสิ่งก่อสร้าง",
            data=item_output,
            file_name=f"ครุภัณฑ์_{month}_{year}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.markdown(
            "<span style='color:red; font-weight:bold;'>กรุณาเลือก เดือน ปี ปีงบประมาณ และไฟล์ที่ต้องการทำความสะอาด ให้ครบถ้วน</span>",
            unsafe_allow_html=True
        )
        

if __name__ == "__main__":
    main()

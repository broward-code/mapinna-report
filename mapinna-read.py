import streamlit as st
import pandas as pd
import xlsxwriter
import base64
import json
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="Mapinna Report Engine", layout="wide")

st.title("🏗️ Mapinna Geotechnical Report Generator")
st.write("Upload the JSON export from the Mapinna app to generate your Field Report.")

# 1. File Uploader for JSON (containing Base64 images)
uploaded_file = st.file_uploader("Upload Mapinna JSON Export", type="json")

if uploaded_file:
    # Load the data
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)
    
    st.success(f"Loaded {len(df)} field observations.")
    st.dataframe(df.drop(columns=['ImageData'], errors='ignore')) # Hide raw base64 from preview

    if st.button("🚀 Generate Excel Field Report"):
        output = BytesIO()
        
        # 2. Initialize Excel Writer
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook  = writer.book
            worksheet = workbook.add_worksheet('Field Log')
            
            # Formats
            header_format = workbook.add_format({
                'bold': True, 'bg_color': '#2F5597', 'font_color': 'white', 'border': 1, 'align': 'center'
            })
            cell_format = workbook.add_format({'border': 1, 'align': 'vcenter'})

            # 3. Define Headers
            headers = ['Photo', 'Site ID', 'Description', 'Coordinates']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Set Column Widths (Photo column needs to be wide)
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:D', 30)

            # 4. Process Rows
            for index, row in df.iterrows():
                row_num = index + 1
                worksheet.set_row(row_num, 120) # Set row height for image

                # Write Text Data
                worksheet.write(row_num, 1, str(row.get('SiteID', '')), cell_format)
                worksheet.write(row_num, 2, str(row.get('Description', '')), cell_format)
                worksheet.write(row_num, 3, str(row.get('Coords', '')), cell_format)

                # Decode and Insert Image
                base64_str = row.get('ImageData', None)
                if base64_str:
                    try:
                        # Strip header if app includes "data:image/png;base64,"
                        if "," in base64_str:
                            base64_str = base64_str.split(",")[1]
                        
                        img_data = base64.b64decode(base64_str)
                        img_buffer = BytesIO(img_data)
                        
                        # Insert image into Cell A (0, row_num)
                        worksheet.insert_image(row_num, 0, 'field_photo.png', {
                            'image_data': img_buffer,
                            'x_scale': 0.15, 
                            'y_scale': 0.15,
                            'x_offset': 5,
                            'y_offset': 5,
                            'positioning': 1 # Move and size with cells
                        })
                    except Exception as e:
                        worksheet.write(row_num, 0, "Error loading image", cell_format)

        # 5. Provide Download
        st.download_button(
            label="💾 Download Excel Report",
            data=output.getvalue(),
            file_name="Mapinna_Field_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

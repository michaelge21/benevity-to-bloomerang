"""
Copyright (c) 2025 AMHC. All rights reserved.
Unauthorized use, distribution, or modification of this software is strictly prohibited.
"""


from flask import Flask, request, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FILE = "combined_benevity.csv"
FINAL_OUTPUT_FILE = "bloomerang_ready.csv"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to clean each CSV
def clean_benevity_csv(file_path):
    df = pd.read_csv(file_path, skiprows=11)  # Skip first 11 rows
    df = df.iloc[:-4, :]  # Remove last four rows
    
    # Ensure that every row containing data in columns C and D is kept
    df = df.dropna(subset=[df.columns[2], df.columns[3], df.columns[4]], how='all')
    
    # Convert Donation Date column to MM/DD/YYYY format (assuming column index 4 is the date column)
    date_col = df.columns[2]  # Ensuring we use the correct column index for Date
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%m/%d/%Y')
    
    return df

# Function to transform Sheet1 into Sheet2 format
def transform_to_bloomerang_format(sheet1_df):
    sheet2_df = pd.DataFrame()
    sheet2_df["Account Number"] = ""  # Sheet2 Column A remains blank
    
    # Map Sheet1 Columns to Sheet2
    sheet2_df["First Name"] = sheet1_df.iloc[:, 3]  # Column D in Sheet1
    sheet2_df["Last Name"] = sheet1_df.iloc[:, 4]  # Column E in Sheet1
    sheet2_df["Organization/Company Name"] = sheet1_df.iloc[:, 0]  # Column A in Sheet1
    
    # Convert Date Column to MM/DD/YYYY format
    sheet2_df["Date"] = pd.to_datetime(sheet1_df.iloc[:, 2], errors='coerce').dt.strftime('%m/%d/%Y')  # Column C in Sheet1
    
    # Sum Sheet1 Columns S and T into Sheet2 Column F (Amount) with numeric conversion
    sheet2_df["Amount"] = sheet1_df.iloc[:, 18].apply(pd.to_numeric, errors='coerce').fillna(0) + \
                           sheet1_df.iloc[:, 19].apply(pd.to_numeric, errors='coerce').fillna(0)  # Columns S and T in Sheet1
    
    # Sheet2 Column G (Fund) is filled with "Unrestricted"
    sheet2_df["Fund"] = "Unrestricted"
    
    # Sheet2 Column H (Transaction Method) is filled with "EFT"
    sheet2_df["Transaction Method"] = "EFT"
    
    # Map Sheet1 Column F to Sheet2 Column J (CUSTOM: Email Freeform)
    sheet2_df["CUSTOM: Email Freeform"] = sheet1_df.iloc[:, 5]  # Column F in Sheet1
    
    # Sheet2 Column K (CUSTOM: Source) is filled with "Benevity"
    sheet2_df["CUSTOM: Source"] = "Benevity"
    
    return sheet2_df

# Route to render upload page
@app.route('/')
def upload_page():
    return '''
    <html>
    <body>
        <h2>AMHC Benevity to Bloomerang App</h2>
        <h2>Upload CSV Files</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="files" multiple>
            <input type="submit" value="Upload and Process">
        </form>
        <p style="text-align:center; font-size:12px;">&copy; 2025 AMHC. All rights reserved.</p>
    </body>
    </html>
    '''

# Route to handle file upload and processing
@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist("files")
    file_paths = []
    
    for file in files:
        if file.filename.endswith(".csv"):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            file_paths.append(file_path)
    
    # Process files
    cleaned_dfs = [clean_benevity_csv(f) for f in file_paths]
    combined_df = pd.concat(cleaned_dfs, ignore_index=True)
    combined_output_path = os.path.join(UPLOAD_FOLDER, OUTPUT_FILE)
    combined_df.to_csv(combined_output_path, index=False)
    
    # Transform to Bloomerang format
    sheet2_df = transform_to_bloomerang_format(combined_df)
    final_output_path = os.path.join(UPLOAD_FOLDER, FINAL_OUTPUT_FILE)
    sheet2_df.to_csv(final_output_path, index=False)
    
    row_count = len(sheet2_df)
    
    return f'''
    <html>
    <body>
        <h2>Upload Successful</h2>
        <p>Your files have been processed successfully.</p>
        <p>Total Rows Processed: {row_count}</p>
        <a href="/">Upload More Files</a>
        <h3>Download Your Processed CSV:</h3>
        <a href="/download">Download Cleaned CSV</a><br>
        <a href="/download_bloomerang">Download Bloomerang-Ready CSV</a>
    </body>
    </html>
    '''

# Route to serve the cleaned CSV file
@app.route('/download')
def download_file():
    return send_file(os.path.join(UPLOAD_FOLDER, OUTPUT_FILE), as_attachment=True)

# Route to serve the Bloomerang-ready CSV file
@app.route('/download_bloomerang')
def download_bloomerang_file():
    return send_file(os.path.join(UPLOAD_FOLDER, FINAL_OUTPUT_FILE), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

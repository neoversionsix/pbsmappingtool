from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import openpyxl
from fuzzywuzzy import fuzz, process
import os
#from werkzeug.utils import secure_filename
import pickle

UPLOAD_FOLDER = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Set a fixed secret key for the session
app.secret_key = os.urandom(24)  # Set a secret key for the session

# Routing for the main page index.html
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')

# Routing for the page 2choosefile1.html
@app.route('/2choosefile1', methods=['GET', 'POST'])
def choose_file_1():
    data_html1 = None  # Initialize data_html1 variable
    if 'file1' in request.files:
        file1 = request.files['file1']
        file1_path = os.path.join(UPLOAD_FOLDER, 'pbsitems.xlsx')  # Define the file path
        file1.save(file1_path)  # Save the file
        data1 = pd.read_excel(file1, engine='openpyxl')
        data_html1 = data1.to_html(index=False)
    return render_template('2choosefile1.html', data_html1=data_html1)

# Routing for the page 3choosefile2.html
@app.route('/3choosefile2', methods=['GET', 'POST'])
def choose_file_2():
    data_html2 = None  # Initialize data_html2 variable
    if 'file2' in request.files:
        file2 = request.files['file2']
        file2_path = os.path.join(UPLOAD_FOLDER, 'pharmacycatalog.xlsx')  # Define the file path
        file2.save(file2_path)  # Save the file
        data2 = pd.read_excel(file2_path, engine='openpyxl')
        data_html2 = data2.head(100).to_html(index=False)
    return render_template('3choosefile2.html', data_html2=data_html2)

# Routing for the page 4mapdata.html
@app.route('/4mapdata', methods=['GET', 'POST'])
def map_data():
    file1_path = os.path.join(UPLOAD_FOLDER, 'pbsitems.xlsx')  # Define the file path
    file2_path = os.path.join(UPLOAD_FOLDER, 'pharmacycatalog.xlsx')  # Define the file path
    # Read the data from the files
    data1 = pd.read_excel(file1_path, engine='openpyxl')
    data2 = pd.read_excel(file2_path, engine='openpyxl')
    
    # Get the first 'PRIMARY' item
    if 'PRIMARY' in data1.columns:
        first_primary = data1['PRIMARY'].iloc[0]
        print(f"First primary: {first_primary}")
    else:
        first_primary = 'PRIMARY column not found in data1'
        print(f"First primary: {first_primary}")    
    # Return the html to the user
    return render_template('4mapdata.html', first_primary=first_primary)


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, g
import pandas as pd
import openpyxl

app = Flask(__name__)

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
        data1 = pd.read_excel(file1, engine='openpyxl')
        g.data1 = data1  # Store data1 in the g objects
        data_html1 = data1.to_html(index=False)
    return render_template('2choosefile1.html', data_html1=data_html1)


# Routing for the page 3choosefile2.html
@app.route('/3choosefile2', methods=['GET', 'POST'])
def choose_file_2():
    data_html2 = None  # Initialize data_html2 variable
    if 'file2' in request.files:
        file2 = request.files['file2']
        data2 = pd.read_excel(file2, engine='openpyxl')
        g.data2 = data2  # Store data2 in the g object
        data_html2 = data2.to_html(index=False)
    return render_template('3choosefile2.html', data_html2=data_html2)


# Routing for the page 4mapdata.html
@app.route('/4mapdata', methods=['GET', 'POST'])
def map_data():
    return render_template('4mapdata.html')

if __name__ == '__main__':
    app.run(debug=True)
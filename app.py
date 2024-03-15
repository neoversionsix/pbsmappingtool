from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    data_html1 = ""
    data_html2 = ""
    if 'file1' in request.files:
        file1 = request.files['file1']
        data1 = pd.read_excel(file1, engine='openpyxl')
        data_html1 = data1.to_html(index=False)
    if 'file2' in request.files:
        file2 = request.files['file2']
        data2 = pd.read_excel(file2, engine='openpyxl')
        data_html2 = data2.head(100).to_html(index=False)
    return render_template('index.html', data_html1=data_html1, data_html2=data_html2)

if __name__ == '__main__':
    app.run(debug=True)
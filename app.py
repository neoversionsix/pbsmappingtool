from flask import Flask, render_template, request, redirect, url_for, session
from flask_caching import Cache
import pandas as pd
import openpyxl
from fuzzywuzzy import fuzz, process
import os
#from werkzeug.utils import secure_filename
import pickle

columns = ['PRIMARY', 'BRAND', 'GENERIC', 'TRADE']  # List of columns to display

UPLOAD_FOLDER = 'uploads'

def fuzzy_logic_df_weighted(input_string, series):
    # Calculate similarity scores
    sort_scores = series.apply(lambda x: fuzz.token_sort_ratio(input_string, x))
    #set_scores = series.apply(lambda x: fuzz.token_set_ratio(input_string, x))

    # Check for first word match and apply additional boost
    first_word_boost = 20  # Define a boost for matching the first word
    first_word_scores = series.apply(
        lambda x: first_word_boost if x.lower().split()[0] == input_string.lower().split()[0] else 0
    )

    # Apply the first word boost to the scores that are less than 100 - first_word_boost
    boosted_scores = pd.Series([min(100, a + w) for a, w in zip(sort_scores, first_word_scores)])

    # Create a dataframe
    df = pd.DataFrame({
        'Value': series,
        'Score': boosted_scores
    })
    # Sort the dataframe by score in descending order
    df = df.sort_values(by='Score', ascending=False)
    return df

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
# app.secret_key = 'your_secret_key'  # Set a fixed secret key for the session
app.secret_key = os.urandom(24)  # Set a secret key for the session
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Routing for the main page index.html
@app.route('/', methods=['GET', 'POST'])
def home():
    session['row_number'] = 0  # Initialize row_number in the session
    session['column_number'] = 0  # Initialize column_number in the session
    return render_template('index.html')

# Routing for the page 2choosefile1.html
@app.route('/2choosefile1', methods=['GET', 'POST'])
def choose_file_1():
    data_html1 = None  # Initialize data_html1 variable
    if 'file1' in request.files:
        file1 = request.files['file1']
        # Define the file path
        file1_path = os.path.join(UPLOAD_FOLDER, 'pbsitems.xlsx')  
        file1.save(file1_path)  # Save the file
        data1 = pd.read_excel(file1_path, engine='openpyxl') # Read to dataframe
        cache.set('data1', data1)  # Store data1 in the cache
        data_html1 = data1.to_html(index=False)
    return render_template('2choosefile1.html', data_html1=data_html1)


# Routing for the page 3choosefile2.html
@app.route('/3choosefile2', methods=['GET', 'POST'])
def choose_file_2():
    data_html2 = None  # Initialize data_html2 variable
    if 'file2' in request.files:
        file2 = request.files['file2']
        # Define the file path
        file2_path = os.path.join(UPLOAD_FOLDER, 'pharmacycatalog.xlsx')
        file2.save(file2_path)  # Save the file
        data2 = pd.read_excel(file2_path, engine='openpyxl')
        #cache.set('data2', data2)  # Store data2 in the cache
        data_html2 = data2.head(20).to_html(index=False)
        

        #Store the catalog items separately (by type) in cache
        df_primaries = data2[data2['ITEM_TYPE'] == 'PRIMARY']
        df_primaries = df_primaries.reset_index(drop=True)  # Reset the index
        cache.set('df_primaries', df_primaries)  # Store df_primaries in the cache

        df_brands = data2[data2['ITEM_TYPE'] == 'BRAND']
        df_brands = df_brands.reset_index(drop=True)  # Reset the index
        cache.set('df_brands', df_brands)  # Store in the cache

        df_generics = data2[data2['ITEM_TYPE'] == 'GENERIC']
        df_generics = df_generics.reset_index(drop=True)  # Reset the index
        cache.set('df_generics', df_generics)  # Store in the cache

        df_trades = data2[data2['ITEM_TYPE'] == 'TRADE']
        df_trades = df_trades.reset_index(drop=True)  # Reset the index
        cache.set('df_trades', df_trades)  # Store in the cache

    return render_template('3choosefile2.html', data_html2=data_html2)

# Routing for the page 4mapdata.html
@app.route('/4mapdata', methods=['GET', 'POST'])
def map_data():
    file1_path = os.path.join(UPLOAD_FOLDER, 'pbsitems.xlsx')
    file2_path = os.path.join(UPLOAD_FOLDER, 'pharmacycatalog.xlsx')

    data1 = cache.get('data1')  # Retrieve data1 from the cache
    #data2 = cache.get('data2')  # Retrieve data2 from the cache
    df_primaries = cache.get('df_primaries')  # Retrieve df_primaries from the cache
    df_brands = cache.get('df_brands')  # Retrieve df_brands from the cache
    df_generics = cache.get('df_generics')  # Retrieve df_generics from the cache
    df_trades = cache.get('df_trades')  # Retrieve df_trades from the cache

    # Get the value of row_number from the session
    row_number = session.get('row_number', 0)
    
    # Get the value of column_number from the session
    column_number = session.get('column_number', 0)

    # List of columns to display
    columns = ['PRIMARY', 'BRAND', 'GENERIC', 'TRADE']
    
    # Get the current column
    current_column = columns[column_number]

    # Get the current item from the current column
    current_item = data1[current_column].iloc[row_number] if current_column in data1.columns else f'{current_column} column not found in data1'

    # Get all the information for the given row
    row_info = data1.iloc[row_number].to_dict()

    # Create the fuzzy logic dataframe
    if current_column == 'PRIMARY':
        df_primaries = cache.get('df_primaries')  # Retrieve df_primaries from the cache
        matches = fuzzy_logic_df_weighted(current_item, df_primaries['NAME']).head(50)
    else:
        matches = pd.DataFrame()  # Empty DataFrame

    return render_template('4mapdata.html',
         current_item=current_item,
         current_column=current_column, 
         row_number=row_number,
         row_info=row_info,
         matches=matches.to_dict('records')  # Convert the DataFrame to a list of dictionaries
         )


# next-save button functionality
@app.route('/save', methods=['POST'])
def save():
    column_number = session.get('column_number', 0)  # Get the value of column_number from the session
    row_number = session.get('row_number', 0)  # Get the value of row_number from the session

    column_number = (column_number + 1) % len(columns)  # Increment column_number and wrap around to 0 when it reaches the end of the columns

    # If column_number wrapped around to 0, increment row_number
    if column_number == 0:
        row_number += 1

    session['column_number'] = column_number
    session['row_number'] = row_number

    return redirect(url_for('map_data'))  # Redirect back to the map_data route

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, session
from flask_caching import Cache
import pandas as pd
import openpyxl
from fuzzywuzzy import fuzz, process
import os
from io import BytesIO
#from werkzeug.utils import secure_filename
import pickle
import pyperclip
import sys

#Global variables
#region
columns = ['PRIMARY', 'BRAND', 'GENERIC', 'TRADE']  # List of columns to display

display_filter_columns = ["NAME", "PRIMARY", "BRAND", "TRADE", "PBS_CODE"]

template = """
;________________________________________________
;  PBS mapping script for PBS_DRUG_ID: MAP_PBS_DRUG_ID_ and SYNONYM_ID: MAP_SYNONYM_ID_
update into pbs_ocs_mapping ocsm
set
    ocsm.beg_effective_dt_tm = cnvtdatetime(curdate, 0004)
    ; Above line sets the activation time to today at 12:04 am, used to identify this type of update
    , ocsm.end_effective_dt_tm = cnvtdatetime("31-DEC-2100")
    /*CHANGE THE ROW BELOW MAP_PBS_DRUG_ID_*/
    , ocsm.pbs_drug_id = MAP_PBS_DRUG_ID_ ; Swap With Pbs Drug Id that maps to the synonym id
    /*CHANGE THE ROW BELOW MAP_SYNONYM_ID_*/
    , ocsm.synonym_id = MAP_SYNONYM_ID_ ; Swap With Synonym Id that maps to the pbs_drug_id
    , ocsm.drug_synonym_id = 0 ; clear multum mapping (multum mappings are not used)
    , ocsm.main_multum_drug_code = 0 ; clear multum mapping
    , ocsm.drug_identifier = "0" ; clear multum mapping
    , ocsm.updt_dt_tm = cnvtdatetime(curdate,curtime3)
    , ocsm.updt_id = reqinfo->updt_id
    , ocsm.updt_cnt = ocsm.updt_cnt + 1
where
    ;Update the next unused row
    ocsm.pbs_ocs_mapping_id =
    (select min(pbs_ocs_mapping_id) from pbs_ocs_mapping where end_effective_dt_tm < sysdate)
    ; Only Update if the item is NOT already mapped
    and not exists
    (
        select 1
        from pbs_ocs_mapping
        /*CHANGE THE ROW BELOW MAP_PBS_DRUG_ID_*/
        where pbs_drug_id = MAP_PBS_DRUG_ID_ ; Swap With Pbs Drug Id
        /*CHANGE THE ROW BELOW MAP_SYNONYM_ID_*/
        and synonym_id = MAP_SYNONYM_ID_ ; Swap With Synonym Id
        and end_effective_dt_tm > sysdate
    )
;________________________________________________
"""
#endregion

#Global Function
#region
def fuzzy_logic_df_weighted(input_string, series):
    # Calculate similarity scores
    sort_scores = series.apply(lambda x: fuzz.token_sort_ratio(input_string, x))

    # Check for first word match and apply additional boost
    first_word_scores = series.apply(
        lambda x: 100 if x.lower().split()[0] == input_string.lower().split()[0] else 0
    )

    # Calculate the weighted average of the first word scores and the total scores
    # with weights of 0.2 and 0.8 respectively 
    # and round to the nearest integer and convert to integer
    weighted_scores = (0.2 * first_word_scores + 0.8 * sort_scores).round().astype(int)

    # Create a dataframe
    df = pd.DataFrame({
        'Value': series,
        'Score': weighted_scores
    })
    # Sort the dataframe by score in descending order
    df = df.sort_values(by='Score', ascending=False)
    return df
#endregion

import pkg_resources

# Set the application path, depending if exe or py file
if getattr(sys, 'frozen', False):
    template_dir = pkg_resources.resource_filename(__name__, 'templates')
else:
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__, template_folder=template_dir)

# app.secret_key = 'your_secret_key'  # Set a fixed secret key for the session
app.secret_key = os.urandom(24)  # Set a secret key for the session
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Routing for the main page index.html
#region
@app.route('/', methods=['GET', 'POST'])
def home():
    session['row_number'] = 0  # Initialize row_number in the session
    session['column_number'] = 0  # Initialize column_number in the session
    index_path = os.path.join(app.template_folder, 'index.html')
    print("Index path:", index_path)
    return render_template('index.html')
#endregion

# Routing for the page 2choosefile1.html
#region
@app.route('/2choosefile1', methods=['GET', 'POST'])
def choose_file_1():
    data_html1 = None  # Initialize data_html1 variable
    if 'file1' in request.files:
        file1 = request.files['file1']
        # Define the file path
        #file1_path = os.path.join(UPLOAD_FOLDER, 'pbsitems.xlsx')  
        #file1.save(file1_path)  # Save the file
        #data1 = pd.read_excel(file1_path, engine='openpyxl') # Read to dataframe
        # Read the file into a BytesIO object
        file1_stream = BytesIO(file1.read())
        # Read the BytesIO object into a pandas DataFrame
        data1 = pd.read_excel(file1_stream, engine='openpyxl')
        cache.set('data1', data1)  # Store data1 in the cache
        data_html1 = data1.to_html(index=False)
    return render_template('2choosefile1.html', data_html1=data_html1)
#endregion


# Routing for the page 3choosefile2.html
#region
@app.route('/3choosefile2', methods=['GET', 'POST'])
def choose_file_2():
    data_html2 = None  # Initialize data_html2 variable
    if 'file2' in request.files:
        file2 = request.files['file2']
        file2_stream = BytesIO(file2.read())
        data2 = pd.read_excel(file2_stream, engine='openpyxl')
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
#endregion

# Routing for the page 4mapdata.html
#region
@app.route('/4mapdata', methods=['GET', 'POST'])
def map_data():
    # Get the final table from the cache, or initialize it if it doesn't exist
    final_table = cache.get('final_table')
    if final_table is None:
        final_table = pd.DataFrame()

    #temp table for display the matches
    if final_table.empty:
        temp_table = pd.DataFrame()
    else:
        temp_table = final_table[display_filter_columns]

    # Convert the current final table to html
    final_table_html = temp_table.to_html(index=False)

    data1 = cache.get('data1')  # Retrieve data1 from the cache
    #data2 = cache.get('data2')  # Retrieve data2 from the cache
    #df_primaries = cache.get('df_primaries')  # Retrieve df_primaries from the cache
    #df_brands = cache.get('df_brands')  # Retrieve df_brands from the cache
    #df_generics = cache.get('df_generics')  # Retrieve df_generics from the cache
    #df_trades = cache.get('df_trades')  # Retrieve df_trades from the cache

    # Get the value of row_number from the session
    row_number = session.get('row_number', 0)
    
    # Get the value of column_number from the session
    column_number = session.get('column_number', 0)
    
    # Get the current column
    current_column = columns[column_number]

    # Get the current item from the current column
    try:
        current_item = data1[current_column].iloc[row_number] if current_column in data1.columns else f'{current_column} column not found in data1'
    except IndexError:
        current_item = f'Row {row_number} not found in data1'
    session['current_item'] = current_item
    # Get all the information for the given row
    try:
        row_info = data1.iloc[row_number].to_dict() # Convert the row to a dictionary
    except IndexError: # Handle the case where the row number is out of range
        row_info = {}
    session['row_info'] = row_info

    # Create the fuzzy logic dataframe
    if current_column == 'PRIMARY':
        df_primaries = cache.get('df_primaries')  # Retrieve df_primaries from the cache
        matches = fuzzy_logic_df_weighted(current_item, df_primaries['NAME']).head(50)
        matches = matches.join(df_primaries, how='left', lsuffix='_match', rsuffix='_original')
    elif current_column == 'BRAND':
        df_brands = cache.get('df_brands')  # Retrieve df_brands from the cache
        matches = fuzzy_logic_df_weighted(current_item, df_brands['NAME']).head(50)
        matches = matches.join(df_brands, how='left', lsuffix='_match', rsuffix='_original')
    elif current_column == 'GENERIC':
        df_generics = cache.get('df_generics')  # Retrieve df_generics from the cache
        matches = fuzzy_logic_df_weighted(current_item, df_generics['NAME']).head(50)
        matches = matches.join(df_generics, how='left', lsuffix='_match', rsuffix='_original')
    elif current_column == 'TRADE':
        df_trades = cache.get('df_trades')  # Retrieve df_trades from the cache
        matches = fuzzy_logic_df_weighted(current_item, df_trades['NAME']).head(50)
        matches = matches.join(df_trades, how='left', lsuffix='_match', rsuffix='_original')
    else:
        matches = pd.DataFrame()  # Empty DataFrame

    matches.reset_index(drop=True, inplace=True)  # Reset the index
    cache.set('matches', matches)  # Store matches in the cache
    matches_dict = matches.reset_index().to_dict('records')

    # Calculate the progress as a percentage of the total number of items
    total_items = (len(data1) * len(columns)) -1
    current_item_number = row_number * len(columns) + column_number
    progress = (current_item_number / total_items) * 100

    # Check if the current row and column are the the last ones 
    is_last_row_and_column = row_number >= len(data1) -1 and column_number >= len(columns) -1
    cache.set('is_last_row_and_column', is_last_row_and_column)

    return render_template('4mapdata.html',
        current_item=current_item,
        current_column=current_column, 
        row_number=row_number,
        row_info=row_info,
        matches=matches_dict,
        final_table_html=final_table_html,
        is_last_row_and_column=is_last_row_and_column,
        progress=progress 
    )
#endregion


# next-save button functionality
#region
@app.route('/save', methods=['POST'])
def save():
    current_item = session.get('current_item', '')  # Get the value of current_item from the session
    row_info = session.get('row_info', {})
    # Get the final table from the cache, or initialize it if it doesn't exist
    final_table = cache.get('final_table')
    if final_table is None:
        final_table = pd.DataFrame()
    column_number = session.get('column_number', 0)  # Get the value of column_number from the session
    row_number = session.get('row_number', 0)  # Get the value of row_number from the session
    # Get the value of is_last_row_and_column from the cache
    is_last_row_and_column = cache.get('is_last_row_and_column')

    if not is_last_row_and_column:
        column_number = (column_number + 1) % len(columns)  # Increment column_number and wrap around to 0 when it reaches the end of the columns
        # If column_number wrapped around to 0, increment row_number
        if column_number == 0:
            row_number += 1

    session['column_number'] = column_number
    session['row_number'] = row_number

    matches = cache.get('matches')  # Retrieve matches from the cache

    # Get the checked matches from the form data
    checked_matches = [key.split('-')[1] for key in request.form if key.startswith('match-') and key != 'save']

    # Add the checked matches to the final table
    for match_index in checked_matches:
        # Convert the match_index to an integer
        match_index = int(match_index)

        # Get the matched row from the matches DataFrame
        match_row = matches.loc[match_index]

        # Create a DataFrame from the current row in data1 and the matched row
        df_to_append = pd.concat([pd.DataFrame([row_info], index=[0]), pd.DataFrame([match_row], index=[0])], axis=1)
        
        # Append the DataFrame to the final table
        final_table = pd.concat([final_table, df_to_append], ignore_index=True)

    # Store the updated final table in the cache
    cache.set('final_table', final_table)

    return redirect(url_for('map_data'))  # Redirect back to the map_data route
#endregion

# routing for the save_end button and final matches page
#region
@app.route('/save_end', methods=['POST'])
def save_end():
    current_item = session.get('current_item', '')  # Get the value of current_item from the session
    row_info = session.get('row_info', {})
    # Get the final table from the cache, or initialize it if it doesn't exist
    final_table = cache.get('final_table')
    if final_table is None:
        final_table = pd.DataFrame()
    matches = cache.get('matches')  # Retrieve matches from the cache

    # Get the checked matches from the form data
    checked_matches = [key.split('-')[1] for key in request.form if key.startswith('match-') and key != 'save']

    # Add the checked matches to the final table
    for match_index in checked_matches:
        # Convert the match_index to an integer
        match_index = int(match_index)

        # Get the matched row from the matches DataFrame
        match_row = matches.loc[match_index]

        # Create a DataFrame from the current row in data1 and the matched row
        df_to_append = pd.concat([pd.DataFrame([row_info], index=[0]), pd.DataFrame([match_row], index=[0])], axis=1)
        
        # Append the DataFrame to the final table
        final_table = pd.concat([final_table, df_to_append], ignore_index=True)

    # Store the updated final table in the cache
    cache.set('final_table', final_table)

    # Make a html table with NAME on the left
    temp_table = final_table.copy()
    if 'NAME' in temp_table.columns:
        name = temp_table.pop('NAME')
        temp_table.insert(0, 'NAME', name)
    
    # Convert the temporary table to html
    final_table_html = temp_table.to_html(index=False)
    
    return render_template('finalmatches.html',
        final_table_html=final_table_html,
    )
#endregion

# routing for the generatecode page
#region
@app.route('/generatecode', methods=['GET', 'POST'])
def generate_code():
    if request.method == 'POST':
        final_table = cache.get('final_table')  # Retrieve final_table from the cache
        final_table_subset = final_table[['MAP_PBS_DRUG_ID_', 'MAP_SYNONYM_ID_']]  # Extract the specified columns

        generated_codes = []
        for _, row in final_table_subset.iterrows():
            code = template
            code = code.replace('MAP_PBS_DRUG_ID_', str(row['MAP_PBS_DRUG_ID_']))
            code = code.replace('MAP_SYNONYM_ID_', str(row['MAP_SYNONYM_ID_']))
            generated_codes.append(code)
        
        output = ('\n' * 3).join(generated_codes)
        pyperclip.copy(output)  # Copy the content to the clipboard
        return render_template('generatecode.html', output=output)
    return render_template('generatecode.html')
#endregion

#if __name__ == "__main__":#This line was messing up launching the app in production
app.run(debug=True)

from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    data_html1 = ""
    data_html2 = ""
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']
        data1 = pd.read_excel(file1, engine='openpyxl')
        data2 = pd.read_excel(file2, engine='openpyxl')
        data_html1 = data1.head(10).to_html(index=False)
        data_html2 = data2.head(10).to_html(index=False)
    return render_template('index.html', data_html1=data_html1, data_html2=data_html2)

if __name__ == '__main__':
    app.run(debug=True)

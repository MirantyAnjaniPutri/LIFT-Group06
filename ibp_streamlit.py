import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import hydralit_components as hc
import datetime

# Set Streamlit to auto full width
st.set_page_config(layout="wide")

# Define function to load factory data
def load_factory_data():
    factory_path = 'D:/After_Campus/Lintasarta/IBP/factory.csv'  # Update with the path to your CSV file
    factory_df = pd.read_csv(factory_path)
    factory_df['datetime on product shipping'] = pd.to_datetime(factory_df['datetime on product shipping'])
    return factory_df

# Define function to load warehouse_movement data
def load_warehouse_movement_data():
    wh_movement = 'D:/After_Campus/Lintasarta/IBP/warehouse_movement.csv'  # Update with the path to your CSV file
    wh_movement = pd.read_csv(wh_movement)
    # wh_movement['datetime on product shipping'] = pd.to_datetime(factory_df['datetime on product shipping'])
    return wh_movement

# Define function to load warehouse_info data
def load_warehouse_info_data():
    wh_info = 'D:/After_Campus/Lintasarta/IBP/warehouse_information.csv'  # Update with the path to your CSV file
    wh_info = pd.read_csv(wh_info)
    # wh_movement['datetime on product shipping'] = pd.to_datetime(factory_df['datetime on product shipping'])
    return wh_info

# Define function to display graph
def display_factory_graph(data, title):
    pivoted_data = pd.pivot_table(
        data,
        values="shipped amount",
        index="datetime on product shipping",
        columns="product name"
    )

    fig = px.bar(
        pivoted_data,
        x=pivoted_data.index,
        y=pivoted_data.columns,
        title='Product Shipping Amount Over Time',
        labels={'datetime on product shipping': 'Date', 'value': 'Shipped Amount'},
        barmode='group'
    )
    fig.update_layout(xaxis_title='Date', yaxis_title='Shipped Amount')
    
    st.plotly_chart(fig)

    st.header(title)
    st.write('Grouped DataFrame:')
    st.write(data)

    st.write('Pivot DataFrame:')
    st.write(pivoted_data)

def clean_warehouse_data(warehouse_movement, warehouse_info):
    pivoted_data_received = pd.pivot_table(
        warehouse_movement,
        values="received amount",
        index=["warehouse_id", "datetime on product arrival"],
        columns="product name"
    )
    pivoted_data_received_new = pivoted_data_received.reset_index()
    pivoted_data_received_new.fillna(0, inplace=True)

    pivoted_data_sold = pd.pivot_table(
        warehouse_movement,
        values="shipping amount",
        index=["warehouse_id", "shipping date"],
        columns="product name"
    )
    pivoted_data_sold_new = pivoted_data_sold.reset_index()
    pivoted_data_sold_new.fillna(0, inplace=True)

    warehouse_capacity = pd.DataFrame(columns=['datetime'])
    # Concatenate and get unique values
    unique_datetime_values = pd.concat([
        pd.DataFrame(pivoted_data_received_new['datetime on product arrival'].unique()),
        pd.DataFrame(pivoted_data_sold_new['shipping date'].unique())
    ])

    # Assign the unique values back to the 'datetime' column of warehouse_capacity
    warehouse_capacity['datetime'] = unique_datetime_values

    # Merge warehouse_capacity and pivoted_data_received_new using a left merge
    jumlah_kapasitas = pd.merge(warehouse_capacity, pivoted_data_received_new, left_on="datetime", right_on="datetime on product arrival")
    # Display the merged DataFrame
    jumlah_kapasitas.drop(columns="datetime on product arrival", inplace=True)
    jumlah_kapasitas = jumlah_kapasitas.drop_duplicates()

    # Merge warehouse_capacity and pivoted_data_received_new using a left merge
    jumlah_kapasitas_1 = pd.merge(warehouse_capacity, pivoted_data_sold_new, left_on="datetime", right_on="shipping date")
    # Display the merged DataFrame
    jumlah_kapasitas_1.drop(columns="shipping date", inplace=True)
    jumlah_kapasitas_1 = jumlah_kapasitas_1.drop_duplicates()
    for column in jumlah_kapasitas_1.columns[2:]:
        # Multiply each non-zero value in the column with -1
        jumlah_kapasitas_1[column] = jumlah_kapasitas_1[column].apply(lambda x: -1 * x if x != 0 else 0)

    new_warehouse_capacity = pd.concat([jumlah_kapasitas, jumlah_kapasitas_1], ignore_index=True)

    # Group data by datetime
    grouped = new_warehouse_capacity.groupby('datetime')
    unique_warehouse_list = new_warehouse_capacity['warehouse_id'].unique()

    # New DataFrame to store the updated data
    new_jumlah_kapasitas = []

    # Iterate over each datetime group
    for datetime, data in grouped:
        # Check if all warehouse IDs are present
        missing_warehouse_ids = set(unique_warehouse_list) - set(data['warehouse_id'])
        
        # Add entries for missing warehouse IDs
        for warehouse_id in missing_warehouse_ids:
            # Create a new entry with zeros for product capacities
            new_entry = {
                "datetime": datetime,
                "warehouse_id": warehouse_id,
                "Detergent A": 0,
                "Detergent H": 0,
                "Drink A": 0,
                "Drink Z": 0,
                "Wafer A": 0,
                "Wafer B": 0,
            }
            new_jumlah_kapasitas.append(new_entry)

    # Convert the list of dictionaries to a DataFrame
    new_jumlah_kapasitas_df = pd.DataFrame(new_jumlah_kapasitas)

    # Concatenate the original DataFrame with the new entries
    new_warehouse_capacity_1 = pd.concat([new_warehouse_capacity, new_jumlah_kapasitas_df], ignore_index=True)
    print(new_warehouse_capacity_1.shape)
    # List of all dates from start to end
    all_dates = pd.date_range(start=new_warehouse_capacity_1['datetime'].min(), end=new_warehouse_capacity_1['datetime'].max(), freq='D')

    # Initialize a set to store missing dates
    missing_dates = set()

    # Iterate over each unique date and warehouse ID combination
    for date in all_dates:
        for warehouse_id in unique_warehouse_list:
            # Check if this combination of date and warehouse ID exists in new_warehouse_capacity
            if not ((new_warehouse_capacity_1['datetime'] == date) & (new_warehouse_capacity_1['warehouse_id'] == warehouse_id)).any():
                # If the combination is missing, add it to the set of missing dates
                missing_dates.add((date, warehouse_id))

    missing_entries = []
    # Iterate over each missing date and add a new entry to new_warehouse_capacity
    for date, warehouse_id in missing_dates:
        new_entry = {'datetime': date, 'warehouse_id': warehouse_id}
        # Set the rest of the columns to 0
        for column in new_warehouse_capacity_1.columns[2:]:
            new_entry[column] = 0
        # Append the new entry to new_warehouse_capacity
        missing_entries.append(new_entry)

    new_warehouse_capacity_2 = pd.concat([new_warehouse_capacity_1, pd.DataFrame(missing_entries)], ignore_index=True)
    new_warehouse_capacity_2.drop_duplicates(inplace=True)
    sorted_warehouse = new_warehouse_capacity_2.sort_values(by=['warehouse_id', 'datetime'])
    sorted_warehouse = sorted_warehouse.reset_index(drop=True)

    # Iterate over the rows starting from the second row
    for index, row in sorted_warehouse.iterrows():
        # Check if it's the first row
        if index == 0:
            continue  # Skip the first row
        
        # Check if the current warehouse_id is the same as the previous row
        if row['warehouse_id'] == sorted_warehouse.at[index - 1, 'warehouse_id']:
            # Iterate over the columns starting from the third column
            for column in sorted_warehouse.columns[2:]:
                # Add the value from the previous row to the current row
                sorted_warehouse.at[index, column] += sorted_warehouse.at[index - 1, column]

    # After the loop, you can calculate the stock column
    sorted_warehouse['stock'] = sorted_warehouse.iloc[:, 2:].sum(axis=1)

    sorted_warehouse = pd.merge(sorted_warehouse, warehouse_info)
    sorted_warehouse.drop(columns=['location', 'leadtime'], inplace=True)

    # Iterate over the rows of the DataFrame
    for index, row in sorted_warehouse.iterrows():
        # Calculate the difference between max_capacity and stock
        difference = row['max_capacity'] - row['stock']
        
        # Check the difference to determine the stock status
        if difference > 5000:
            status = 'Understock'
        elif difference >= 0 and difference <= 1000:
            status = 'Overstock'
        else:
            status = 'Safestock'
        
        # Assign the stock status to a new column named "stock_status"
        sorted_warehouse.at[index, 'stock_status'] = status

    return sorted_warehouse

def update_chart(warehouse_id, cleaned_wh):
    # Filter the DataFrame to include only the data for the selected warehouse
    filtered_group = cleaned_wh[cleaned_wh['warehouse_id'] == warehouse_id]

    # Create a bar-line chart
    fig = px.line(filtered_group, x='datetime', y='max_capacity', labels={'datetime': 'Datetime', 'max_capacity': 'Maximum Capacity'})
    fig.add_bar(x=filtered_group['datetime'], y=filtered_group['stock'], name='Stock')

    # Show the chart
    st.plotly_chart(fig)

def display_warehouse_graph(cleaned_wh, header):
    # Get unique warehouse_id values
    unique_warehouse_ids = cleaned_wh['warehouse_id'].unique()

    # Create a list of buttons for the dropdown menu
    buttons = []
    for warehouse_id in unique_warehouse_ids:
        buttons.append(dict(label=str(warehouse_id),
                            method="update",
                            args=[{"visible": [warehouse_id == id for id in unique_warehouse_ids]},
                                {"title": f"Stock and Max Capacity for Warehouse {warehouse_id}"}]))

    # Add the buttons to the layout
    updatemenus = [dict(buttons=buttons,
                        direction="down",
                        showactive=True,
                        x=0.1,
                        xanchor="left",
                        y=1.15,
                        yanchor="top")]

    # Display the dropdown menu and update the chart based on the selected warehouse
    selected_warehouse = st.selectbox('Select Warehouse', unique_warehouse_ids, index=0)
    update_chart(selected_warehouse, cleaned_wh)

    st.header(header)
    st.write('Warehouse Movement:')
    st.write(cleaned_wh)

def display_warehouse_info_graph(warehouse_info, cleaned_df, header):
    st.header(header)
    st.write('Warehouse Information:')
    
    # Get today's date
    today = datetime.date.today()

    # Convert the 'datetime' column to date format
    cleaned_df['datetime'] = pd.to_datetime(cleaned_df['datetime'])
    cleaned_df['date'] = cleaned_df['datetime'].dt.date

    # Check if any date matches today
    is_today = cleaned_df['date'] == today

    # Get the rows where the date matches today
    today_rows = cleaned_df[is_today]

    # Iterate over each row in warehouse_info
    for index, row in warehouse_info.iterrows():
        # Initialize today_status
        today_status = 'Understock'
        
        # Check if there are today's rows and if the warehouse_id matches
        if not today_rows.empty and row['warehouse_id'] in today_rows['warehouse_id'].values:
            # Get the stock_status for the corresponding warehouse_id and today's date
            today_status = today_rows[today_rows['warehouse_id'] == row['warehouse_id']]['stock_status'].iloc[0]
        
        # Assign the status for today to the 'Status' column in warehouse_info
        warehouse_info.at[index, 'Status'] = today_status

    # Define custom colors for each status category
    custom_colors = px.colors.qualitative.Set3

    # Group the warehouse_info DataFrame by 'Status' and count the occurrences of each status
    status_counts = warehouse_info['Status'].value_counts()

    # Create a donut chart with custom colors
    fig = px.pie(status_counts, 
                values=status_counts.values, 
                names=status_counts.index, 
                hole=0.5, 
                title='Warehouse Status Distribution',
                color=status_counts.index,  # Assign custom colors to each status category
                color_discrete_map={status: color for status, color in zip(status_counts.index, custom_colors)})

    # Update layout for better readability
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(showlegend=True)

    # Display the chart in the Streamlit app
    st.write(fig)
    st.write(warehouse_info)


# def add_data(type, data, loaded_df):
#     if type == 'factory':
#         path = 'D:/After_Campus/Lintasarta/IBP/factory.csv'

#     elif type == 'wh_movement':
#         path = 'D:/After_Campus/Lintasarta/IBP/warehouse_movement.csv'

#     elif type == 'wh_info':
#         path = 'D:/After_Campus/Lintasarta/IBP/warehouse_information.csv'
    
#     if data.columns == loaded_df.columns:
#         combined_data = pd.concat([data, loaded_df], ignore_index=True)
#         combined_data.to_csv(path, index=False)
#     else:
#         st.error("Column names of uploaded CSV file do not match the existing data.")

def main():
    # Define menu items
    menu_data = [
        {'label': "Factory"},
        {'label': "Warehouse Movement"},
        {'label': "Warehouse Info"},
    ]

    # Create navigation bar
    menu_id = hc.nav_bar(menu_definition=menu_data)

    factory_df = load_factory_data()
    wh_movement = load_warehouse_movement_data()
    wh_info = load_warehouse_info_data()
    cleaned_wh = clean_warehouse_data(wh_movement, wh_info)

    # Load appropriate data based on menu selection
    if menu_id == 'Factory':
        st.title("Factory Data Visualization")
        display_factory_graph(factory_df, "Factory Data")
        # upload_file = st.file_uploader("Upload CSV file to update Factory Data", type="csv")
        # if upload_file is not None:
        #     add_data('factory', upload_file, factory_df)
        
    elif menu_id == 'Warehouse Movement':
        st.write("Warehouse Dataframe")
        display_warehouse_graph(cleaned_wh, "Warehouse Visualization")
        # data = load_warehouse_movement_data()
        # display_graph(data, "Warehouse Movement Data Visualization")
    elif menu_id == 'Warehouse Info':
        display_warehouse_info_graph(wh_info, cleaned_wh, "Warehouse Information Visualization")
        # data = load_warehouse_info_data()
        # display_graph(data, "Warehouse Info Data Visualization")

if __name__ == '__main__':
    main()

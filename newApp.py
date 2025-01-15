import gspread
import streamlit as st
import datetime
import pandas as pd

# Connect to Google Sheets
Sheet_credential = gspread.service_account("credential.json")
spreadsheet = Sheet_credential.open_by_key('1FLriyowMmKSBaIZVpI0akL3uCin7Eulryld3ZsGQUj8')

# Fetch data from Google Sheets
def fetch_data():
    sheet = spreadsheet.sheet1
    return pd.DataFrame(sheet.get_all_records())

def show_home_page():
    st.title("Welcome to the Fitness App!")
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    st.subheader(f"Today's date is {current_date}")
    st.divider()
   

    # Fetch the workout data
    df = fetch_data()

    if df.empty:
        st.write("No workout data available.")
        return

    # Normalize column names
    df.columns = df.columns.str.lower()

    # Ensure distance and date are numeric
    df["distance"] = pd.to_numeric(df["distance"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"])

    # Filter data for the past week (7 days)
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    df_last_week = df[df["date"] >= one_week_ago]

    if df_last_week.empty:
        st.write("No workouts in the past week.")
        return

    # Calculate the total distance per workout type for the past week
    workout_distances = df_last_week.groupby("workout_type")["distance"].sum().reset_index()

    # Identify the most used workout type (with the maximum distance)
    most_used_workout = workout_distances.loc[workout_distances["distance"].idxmax()]

    # Display the most used workout type and its distance
    st.subheader(f"Your Most Used Workout Type in the Past Week was {most_used_workout['workout_type']}!")
    st.write(f"Total Distance: {most_used_workout['distance']} km")

    # Display the data in a bar chart
    st.subheader("Workout Types and Total Distance in the Past Week")
    st.bar_chart(workout_distances.set_index("workout_type")["distance"])
    st.divider()

    # Display details of the last workout
    last_workout = df.sort_values(by="date", ascending=False).iloc[0]

    # Display the last workout in a card format like in the "View Workouts" page
    st.subheader("Last Workout Details:")
    st.markdown(f"""
    <div style="border: 1px solid #ccc; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <p style="font-size: 18px; line-height: 1.6;">
            <strong>Workout Type:</strong> {last_workout['workout_type']}<br>
            <strong>Name:</strong> {last_workout['name']}<br>
            <strong>Date:</strong> {last_workout['date']}<br>
            <strong>Duration:</strong> {last_workout['duration']} min<br>
            <strong>Distance:</strong> {last_workout['distance']} km<br>
            <strong>Details:</strong> {last_workout['details']}<br>
        </p>
    </div>
    """, unsafe_allow_html=True)



# Add Workout page
def show_add_workout_page():
    st.title("Add a New Workout")

    # Choosing Workout Type
    st.subheader("Choose Workout Type:")
    options = ["Running", "Swimming", "Biking", "Weights", "Other"]
    workout_type = st.radio("Workout Type", options)
    st.write(f"You selected: {workout_type}")
    st.divider()

    # Naming Workout
    st.subheader("Enter Workout Name:")
    name = st.text_input("Workout Name", "Today's Workout")
    st.write(f"Workout name: {name}")
    st.divider()

    # Date
    st.subheader("Select a Date for the Workout:")
    date = st.date_input("Workout Date", datetime.date.today())
    st.write(f"Workout date selected: {date}")
    st.divider()

    # Duration
    st.subheader("Enter Duration of Workout:")
    duration = st.number_input("Duration (Min):", min_value=0, step=1)
    st.write(f"Duration entered: {duration} minutes")
    st.divider()

    # Distance
    st.subheader("Enter Distance of Workout:")
    distance = st.number_input("Distance (Km):", min_value=0.0, step=0.1)
    st.write(f"Distance entered: {distance} Km")
    st.divider()

    # Details
    st.subheader("Enter Any Details About Your Workout")
    details = st.text_area("Details:", "")
    st.divider()

    # Save data to Google Sheet
    if st.button("Save Workout"):
        try:
            row = [
                workout_type,  
                name,              
                str(date),
                duration,          
                distance or "-",  
                details or "-",  
            ]

            # Append the row to the first sheet in the spreadsheet
            sheet = spreadsheet.sheet1
            sheet.append_row(row)
            st.success("Workout saved successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")


#Delete Workout Function
def delete_workout(idx):
    try:
        sheet = spreadsheet.sheet1
        sheet.delete_rows(idx + 2)  
        st.success("Workout deleted!")
    except Exception as e:
        st.error(f"An error occurred while deleting: {e}")

# View Workouts Page
def show_view_workouts_page():
    st.title("View Workouts")
    df = fetch_data()  
    if not df.empty:
        df.columns = df.columns.str.lower()

        #Convert distance to numeric
        df["distance"] = pd.to_numeric(df["distance"], errors="coerce").fillna(0)

        #Filter and Sort
        st.subheader("Filter Workouts")
        workout_types = ["All"] + df["workout_type"].unique().tolist()
        selected_type = st.selectbox("Select Workout Type", workout_types)

        sort_options = ["None", "Distance", "Recent"]
        sort_by_selection = st.selectbox("Sort Workouts By", sort_options)

        #Apply filters
        filtered_df = df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["workout_type"] == selected_type]

        if sort_by_selection == "Distance":
            filtered_df = filtered_df.sort_values(by="distance", ascending=False)
        elif sort_by_selection == "Recent":
            filtered_df = filtered_df.sort_values(by="date", ascending=False)

        #Display workouts
        if filtered_df.empty:
            st.write("No workouts found.")
        else:
            num_columns = 2
            cols = st.columns(num_columns)

            for idx, row in filtered_df.iterrows():
                #Display workout details
                with cols[idx % num_columns]:
                    st.markdown(f"""
                    <div style="border: 1px solid #ccc; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <p style="font-size: 18px; line-height: 1.6;">
                            <strong>Workout Type:</strong> {row['workout_type']}<br>
                            <strong>Name:</strong> {row['name']}<br>
                            <strong>Date:</strong> {row['date']}<br>
                            <strong>Duration:</strong> {row['duration']} min<br>
                            <strong>Distance:</strong> {row['distance']} km<br>
                            <strong>Details:</strong> {row['details']}<br>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col2:
                        if st.button("Delete", key=f"delete_{idx}"):
                            delete_workout(idx)

    else:
        st.write("No workouts recorded yet. Add some from the 'Add Workout' page.")

import datetime
import pandas as pd
import streamlit as st

def show_create_workout_graph():
    st.title("Create Workout Graph")

    # Fetch the latest data
    df = fetch_data()

    if df.empty:
        st.warning("No workout data available to create graphs.")
        return

    # Normalize column names and ensure proper data types
    df.columns = df.columns.str.lower()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date  # Ensure date is in proper format (date only)
    df["distance"] = pd.to_numeric(df["distance"], errors="coerce").fillna(0)
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0)

    # Filter options
    st.subheader("Filter Options")

    # Workout Type Filter
    workout_types = ["All"] + df["workout_type"].unique().tolist()
    selected_type = st.selectbox("Select Workout Type:", workout_types)

    # Time Period Filter
    time_periods = ["Past Week", "Past Month", "Past Year"]
    selected_period = st.radio("Select Time Period:", time_periods)

    # Graph Parameter
    graph_parameter = st.radio("Graph Parameter:", ["Duration", "Distance"])

    # Apply workout type filter
    if selected_type != "All":
        df = df[df["workout_type"] == selected_type]

    # Get current date
    current_date = datetime.datetime.now().date()

    # Filter and group data based on selected period
    if selected_period == "Past Week":
        # Calculate the start of the week (Monday) and end of the week (Sunday)
        week_start = current_date - datetime.timedelta(days=current_date.weekday())  # Monday
        week_end = week_start + datetime.timedelta(days=6)  # Sunday
        df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]
        df["period"] = df["date"].astype(str)  # Convert date to string for grouping

    elif selected_period == "Past Month":
        past_month_start = current_date - datetime.timedelta(days=30)
        df = df[df["date"] >= past_month_start]
        df["period"] = df["date"].astype(str)  # Convert date to string for grouping

    elif selected_period == "Past Year":
        past_year_start = current_date - datetime.timedelta(days=365)
        df = df[df["date"] >= past_year_start]
        df["period"] = df["date"].astype(str)  # Convert date to string for grouping

    # Group by period and aggregate data
    graph_data = df.groupby("period")[graph_parameter.lower()].sum().reset_index()

    # Display both line and bar charts
    if not graph_data.empty:
        st.subheader(f"{graph_parameter} over {selected_period}")
        st.line_chart(data=graph_data.set_index("period"))
        st.bar_chart(data=graph_data.set_index("period"))
    else:
        st.write("No data available for selected filters.")






# Sidebar selection
def main():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page", ["Home", "Add Workout", "View Workouts", "Create Workout Graph"])

    # Show content based on selected page
    if page == "Home":
        show_home_page()
    elif page == "Add Workout":
        show_add_workout_page()
    elif page == "View Workouts":
        show_view_workouts_page()
    elif page == "Create Workout Graph":
        show_create_workout_graph()

# Run the app
if __name__ == "__main__":
    main()
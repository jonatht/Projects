#!/usr/bin/env python
# coding: utf-8

# In[45]:


import glob
import pandas as pd
import numpy as np

# Function to Check if any rows have a duplicated primary key
def check_duplicate_primary_key(df, primary_key):
    
    
    duplicated_rows = df[df.duplicated(subset=[primary_key], keep=False)]
    
    return duplicated_rows

 #Function to remove non numeric values from numeric fields
def non_numeric(df, column_name):
  
    non_numeric= ~df[column_name].apply(lambda x: isinstance(x, (int, float)))

    
    df.loc[non_numeric, column_name] = np.nan

    return df

#Function Checking column name
def check_column_names(df, standard_columns):
   
    incorrect_column_names = [column_name for column_name in df.columns if column_name not in standard_columns]
    return incorrect_column_names

#renaming incorrect column names
def rename_column(df, predefined_column_names):
    for i, col_name in enumerate(standard_columns):
        if col_name != df.columns[i]:
            df.rename(columns={df.columns[i]: col_name}, inplace=True)
    return df



#checking invalid date
def convert_date_columns(df, column_name):
   
    try:
        pd.to_datetime(df[column_name], errors='raise')
        
        df[column_name] = pd.to_datetime(df[column_name]).dt.strftime('%Y-%m-%d')
        
        return df
    except ValueError:
        
        df[column_name] = df[column_name].apply(lambda x: '' if x != '' else x)
        return df

#check if Date is valid
import datetime

def validate_date(df, date_column):
   
    
    current_year = datetime.datetime.now().year
    min_year = 1900
    df[date_column] = pd.to_datetime(df[date_column])
    
    for date in df[date_column]:
        if date.year < min_year or date.year > current_year:
                df[date_column] = df[date_column].replace(date, "")
        
    return df



#reading data from locations file
loc=pd.read_csv("/Users/jonath/Documents/data/location_mapping.csv")
duplicated_rows = check_duplicate_primary_key(loc, 'id')
if not duplicated_rows.empty:
    print("Duplicate primary key found in the following rows:")
    print(duplicated_rows)
    # the location duplication should halt the script 
loc=loc.drop_duplicates() #removing duplicate location encountered

#reading data from leavers file
leave=pd.read_csv("/Users/jonath/Documents/data/leavers.csv")
duplicated_rows = check_duplicate_primary_key(leave, 'employee_id')
if not duplicated_rows.empty:
    print("Duplicate primary key found in the following rows:")
    print(duplicated_rows)
    #duplication should halt the script 
leave=leave.drop_duplicates()#removing duplicates

leave=convert_date_columns(leave,'leave_date')#validating and formating date column
leave=validate_date(leave,'leave_date')
leave["leave_month"] = pd.to_datetime(leave['leave_date'],format='%Y-%m-%d').dt.month #to get leaving month
leave["leave_year"] = pd.to_datetime(leave['leave_date'],format='%Y-%m-%d').dt.year 

#accessing all files with name core in folder
csv_files = glob.glob("/Users/jonath/Documents/data/core_*.csv")
dates = [date.split("_")[1].split(".")[0] for date in csv_files] #creating a list of dates from file names to loop through 
dates = sorted(dates)

#loop to extract all core files
for date in dates:
   
    filename = f"/Users/jonath/Documents/data/core_{date}.csv"
    core = pd.read_csv(filename)
    standard_columns=['job_id', 'employee_id', 'position_id', 'target_bonus', 'first_name',
       'last_name', 'gender', 'date_of_birth', 'date_in_service',
       'date_in_position', 'fte', 'employee_status', 'employee_grade', 'title',
       'position_grade', 'solid_line', 'dotted_line', 'business_unit_level0',
       'business_unit_level1', 'business_unit_level2', 'business_unit_level3',
       'functional_area_level0', 'functional_area_level1',
       'functional_area_level2', 'functional_area_level3', 'contract_type',
       'retention_risk', 'retention_risk_reason', 'solid_line_layer',
       'base_salary', 'relative_salary_position', 'currency',
       'absence_frequency_rolling', 'absence_duration_days',
       'absence_open_since', 'cost_center_level0', 'cost_center_level1',
       'cost_center_level2', 'cost_center_level3', 'legal_entity_level0',
       'legal_entity_level1', 'legal_entity_level2', 'legal_entity_level3',
       'location_id', 'hire_channel', 'hire_type', 'hire_reason_level0',
       'hire_reason_level1', 'hire_date'] #list of correct column names observed from multiple files
    
    #validating column names
    wrong_column_names = check_column_names(core, standard_columns)
    if wrong_column_names:
        print(f"The following column names in file core_{date} are incorrect:")
        print(wrong_column_names)
     #renaming wrong column names
    core=rename_column(core,standard_columns) 
    date_dt = pd.to_datetime(date)
    year = date_dt.year#get year
    prev = year-1 #get previous year
    month=date_dt.month #get month
     
        #filling missing values 
    core['gender']=core['gender'].replace({'F':'Female','M':'Male'})
    core['gender']=core['gender'].fillna('Missing')
   

    #combining location and core files
    core_new=pd.merge(core,loc,left_on="location_id",right_on="id",how="left")

    #validating and formating date columns
    core_new = validate_date(core_new,'date_of_birth')
    core_new = convert_date_columns(core_new,'date_of_birth')
    core_new = validate_date(core_new,'date_in_service')
    core_new = convert_date_columns(core_new,'date_in_service')
    core_new = validate_date(core_new,'date_in_position')
    core_new = convert_date_columns(core_new,'date_in_position')
    core_new = validate_date(core_new,'hire_date')
    core_new = convert_date_columns(core_new,'hire_date')
    
    #validation to ensure numeric fields dont have non numeric values
    core_new=non_numeric(core_new,'base_salary')
    core_new=non_numeric(core_new,'target_bonus')
    
    
   
    #block to determine 'added as hire'
    
    core_new["hire_year"] = pd.to_datetime(core_new['hire_date'],format='%Y-%m-%d').dt.year
    core_new["hire_month"] = pd.to_datetime(core_new['hire_date'],format='%Y-%m-%d').dt.month
    core_new["added_as_hire"]= (core_new["hire_year"]==year) & (core_new["hire_month"]==month)
   
    #hire_date had a lot of empty values so a second block using date_in_service was used if hire_date is empty
    core_new["month_in_service"] = pd.to_datetime(core_new['date_in_service'],format='%Y-%m-%d').dt.month
    core_new["year_in_service"] = pd.to_datetime(core_new['date_in_service'],format='%Y-%m-%d').dt.year
    condition= core_new['hire_date'].isna() | (core_new['hire_date'] == '')
    if condition.any():
        core_new["added_as_hire"]= (core_new["year_in_service"]==year) & (core_new["month_in_service"]==month)
    
    #block connecting core file with leaver's file
    leave_now= leave[(leave["leave_year"]==year) & (leave["leave_month"]==month)]
    core_new2=pd.merge(core_new,leave_now,on="employee_id",how="left")
    core_new2=core_new2.drop(columns=['id','leave_month','leave_year','month_in_service','year_in_service','hire_year','hire_month'])#removing unnecessary and repeating columns 
    
    #logic to connect core file with most recent talent file
    if month >= 2 and month <8:
        talent = pd.read_csv(f"/Users/jonath/Documents/data/talent_{year}-02.csv")
    elif month < 2:
        talent = pd.read_csv(f"/Users/jonath/Documents/data/talent_{prev}-08.csv")
    else:
        talent = pd.read_csv(f"/Users/jonath/Documents/data/talent_{year}-08.csv")
       
       #checking duplicates in talent files
    duplicated_rows = check_duplicate_primary_key(talent, 'employee_id')
    
    if not duplicated_rows.empty:
        print("Duplicate primary key found in the following rows:")
        print(duplicated_rows)
    talent=talent.drop_duplicates() #removing duplicates
     
        #combining core and talent file
    core_new3=pd.merge(core_new2,talent,left_on="employee_id",right_on="employee_id",how="left")
   
    #count validation
    if len(core_new)!= len(core_new3):
        print("Count Mismatch in Core file:")
        print(len(core_new3))
       
    #date logical validation
    core_new3['leave_date'] = pd.to_datetime(core_new3['leave_date'])
    core_new3['hire_date'] = pd.to_datetime(core_new3['hire_date'])
    core_new3['date_in_service'] = pd.to_datetime(core_new3['date_in_service'])
    comparison_result = (core_new3['leave_date'] < core_new3['hire_date']) | (core_new3['leave_date'] < core_new3['date_in_service'])

   
    invalid_rows = core_new3[comparison_result]

  
    if not invalid_rows.empty:
        print("Leave Date Cannot be before Date of Joining")
        print(invalid_rows[['leave_date', 'hire_date','date_in_service']])
   
    #writing to csv file   
    filename1 = f"/Users/jonath/Documents/test/core_{date}.csv"
    core_new3.to_csv(filename1, sep=";", index=False)
    
   





# In[ ]:





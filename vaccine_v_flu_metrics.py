import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# This script will have functions that generate the vaccine and flu metrics by state
# The task will involve putting together dataframes and joining them.


def load_vax_data(filename):
    """Extract the rows and columns that we want for this project."""
    raw_df = pd.read_csv(filename)
    df = raw_df.loc[raw_df['Geography Type'] == 'States/Local Areas']
    # Get the aggregate data for all types of vaccines
    df = df.loc[df['Vaccine'] == 'Seasonal Influenza']
    # Fill in nans
    df.fillna('0', inplace=True)
    # Get the data broken down by age
    df = df.loc[df['Dimension Type'] == 'Age']
    # Except the flu data is not broken down by age. There are fields to break it down possibly in the future, but for
    # now we will just look at all ages
    df = df.loc[df['Dimension'] == '>=6 Months']
    df['data'] = df['Estimate (%)'].apply(str) + '__' + df['95% CI (%)'] + '__' + df['Sample Size'].apply(str)
    final_df = df.groupby(['Geography', 'Season/Survey Year']).agg({'data': 'max'}).reset_index()
    final_df['Estimate (%)'] = final_df['data'].apply(lambda x: x.split('__')[0])
    final_df['95% CI (%) Low'] = final_df['data'].apply(lambda x: x.split('__')[1].split(' to ')[0])
    final_df['95% CI (%) High'] = final_df['data'].apply(lambda x: x.split('__')[1].split(' to ')[-1])
    final_df['Sample Size'] = final_df['data'].apply(lambda x: x.split('__')[2])
    fields = ['Geography', 'Season/Survey Year', 'Estimate (%)', '95% CI (%) Low', '95% CI (%) High', 'Sample Size']
    final_df = final_df[fields]
    final_df.rename(columns={'Geography': 'REGION'}, inplace=True)
    # Convert the data fields to numerical typing
    final_df.replace('0', np.NaN, inplace=True)
    final_df[['Estimate (%)', '95% CI (%) Low', '95% CI (%) High', 'Sample Size']] = \
        final_df[['Estimate (%)', '95% CI (%) Low', '95% CI (%) High', 'Sample Size']].apply(lambda x: x.apply(float))
    final_df['Sample Size'] = final_df['Sample Size'].apply(int)
    return final_df


def convert_time_to_seasons(year_week_df):
    """Converts the year and week number from flu df to season/survey year and month which matches the vaccine df"""
    # Convert week numbers to datetime objects
    year_week_df['date'] = pd.to_datetime(
        'Fri ' + year_week_df['WEEK'].astype(str) + ' ' + year_week_df['YEAR'].astype(str),
        format='%a %U %Y')
    # Extract month from datetime objects
    year_week_df['Month'] = year_week_df['date'].dt.month
    year_week_df['Season/Survey Year'] = year_week_df['YEAR'].astype(str)
    # The season starts at month 8 (Aug)
    season_start_df = year_week_df.loc[year_week_df['Month'] >= 8]
    season_start_df['end year'] = season_start_df['YEAR'].apply(lambda x: str(x + 1)[-2:])
    season_start_df['Season/Survey Year'] = season_start_df['YEAR'].astype(str) + '-' + season_start_df['end year']
    year_week_df.loc[year_week_df['Month'] >= 8, 'Season/Survey Year'] = season_start_df['Season/Survey Year']

    season_end_df = year_week_df.loc[year_week_df['Month'] < 8]
    season_end_df['start year'] = season_end_df['YEAR'].apply(lambda x: x - 1)
    season_end_df['Season/Survey Year'] = season_end_df['start year'].astype(str) + '-' + \
                                          season_end_df['YEAR'].apply(lambda x: str(x)[-2:])
    year_week_df.loc[year_week_df['Month'] < 8, 'Season/Survey Year'] = season_end_df['Season/Survey Year']
    return year_week_df[['Season/Survey Year', 'Month']]


def load_flu_test_data(filenames):
    """There are two files, one for prior to 2015 and one for after 2015. Combine into a single
    dataframe, extract the rows and columns that we want for this project. Must also adjust columns
    to match the vaccination dataframe, in particular how time is tracked."""
    raw_df_0 = pd.read_csv(filenames[0], header=1)
    raw_df_1 = pd.read_csv(filenames[1], header=1)
    flu_fields = ['REGION', 'YEAR', 'WEEK', 'TOTAL SPECIMENS', 'PERCENT POSITIVE']
    df = pd.concat([raw_df_0[flu_fields], raw_df_1[flu_fields]])
    # Convert the Year and Week to Season/Survey Year and Month
    flu_season_df = convert_time_to_seasons(df[['YEAR', 'WEEK']])
    df[['Season/Survey Year', 'Month']] = flu_season_df
    flu_fields = ['REGION', 'Season/Survey Year', 'Month', 'TOTAL SPECIMENS', 'PERCENT POSITIVE']
    df = df[flu_fields]
    # Data is by week, but we want to aggregate by month for each state.
    # Treat all NaN (X) as 0
    df.replace('X', 0, inplace=True)
    df['TOTAL SPECIMENS'] = df['TOTAL SPECIMENS'].apply(int)
    df['PERCENT POSITIVE'] = df['PERCENT POSITIVE'].apply(float)
    df['TOTAL POSITIVE'] = (df['TOTAL SPECIMENS'] * df['PERCENT POSITIVE'] * 0.01).round().astype(int)
    assert isinstance(df.groupby(['REGION', 'Season/Survey Year']).agg, object)
    out_df = df.groupby(['REGION', 'Season/Survey Year']).agg({'TOTAL SPECIMENS': 'sum',
                                                               'TOTAL POSITIVE': 'sum'}).reset_index()
    return out_df


def load_ili_hospital_data(filename):
    df = pd.read_csv(filename, header=1)
    df[['Season/Survey Year', 'Month']] = convert_time_to_seasons(df[['YEAR', 'WEEK']])
    df.replace('X', 0, inplace=True)
    df['ILITOTAL'] = df['ILITOTAL'].apply(int)
    df['TOTAL PATIENTS'] = df['TOTAL PATIENTS'].apply(int)
    out_df = df.groupby(['REGION', 'Season/Survey Year']).agg({'ILITOTAL': 'sum',
                                                               'TOTAL PATIENTS': 'sum'}).reset_index()
    return out_df


def join_export_dfs(vax, flu, ili, outfile):
    df = pd.merge(vax, flu, left_on=['REGION', 'Season/Survey Year'], right_on=['REGION', 'Season/Survey Year'])
    df = pd.merge(df, ili, left_on=['REGION', 'Season/Survey Year'], right_on=['REGION', 'Season/Survey Year'])
    df.to_csv(outfile, index=False)


if __name__ == '__main__':
    vax_df = load_vax_data('data/Influenza_Vaccination_Coverage_for_All_Ages__6__Months_.csv')
    flu_files = ['data/WHO_NREVSS_Combined_prior_to_2015_16.csv',
                 'data/WHO_NREVSS_Clinical_Labs.csv']
    flu_df = load_flu_test_data(flu_files)
    ili_df = load_ili_hospital_data('data/ILINet.csv')
    join_export_dfs(vax_df, flu_df, ili_df, 'data/data.csv')

import pandas as pd

vaccine_df = pd.read_csv('data/Influenza_Vaccination_Coverage_for_All_Ages__6__Months_.csv')
flu_post2015_df = pd.read_csv('data/WHO_NREVSS_Clinical_Labs.csv', header=1)
flu_pre2015_df = pd.read_csv('data/WHO_NREVSS_Combined_prior_to_2015_16.csv', header=1)
vaccine_states = set(pd.unique(vaccine_df['Geography']))

flu_fields = ['REGION', 'YEAR', 'WEEK', 'TOTAL SPECIMENS', 'PERCENT POSITIVE']
flu_df = pd.concat([flu_pre2015_df[flu_fields], flu_post2015_df[flu_fields]])
flu_states = set(pd.unique(flu_df['REGION']))
states = vaccine_states.intersection(flu_states)
print(vaccine_df.nunique())

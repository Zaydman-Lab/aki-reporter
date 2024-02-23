'''
analytics.py

Mark A. Zaydman
10.28.2022

Purpose: Module of analytical tools for identifying aki samples and encounters given Cr data pulled from the LIS

Functions:

  main()->pd.DataFrame -  main function, will evoke subordinate functions to generate processed data
  clean_data(df: pd.DataFrame)->pd.DataFrame -> returns data cleaned of test/cap samples, and nan results, and with casting key datatypes
  calc_encounter_baseline(row: pd.Series, df: pd.DataFrame)->pd.Series: Returns lowest previous cr for this encounter
  calc_twoday_baseline(row: pd.Series,df: pd.DataFrame)->pd.Series: Returns lowest previous cr within the past 48 hours
  encode_race(race_str: str)->float: Returns 1.212 it pt race is black else 1
  encode_sex(sex_str: str)->float: Returns sex coefficient for mdrd - 0.72 if female, 1 if male, else None
  calc_mdrd_baseline(row: pd.Series)->float: Returns estimated creatinine using mdrd formula if pt demographics are known, else None
  stage_aki(result_val: float, baseline: float)->str: Returns stage of AKI according to KDIGO criteria
  apply_kdigo(result_val: float,baseline: float,twoday_baseline)->str: returns stage if KDIGO criteria satisfied, else False
  is_aki(row: pd.Series)->int: returns 1 if sample meets KDIGO aki critera, else 0
  aki_encounter(row: pd.Series,df:pd.DataFrame)->bool: Return True if any sample from this encounter is aki else false

  
'''

#%% imports 
import queries
import pandas as pd
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates
from datetime import date,timedelta

#%% helper functions
def clean_data(df: pd.DataFrame)->pd.DataFrame:
  '''returns cleaned copy of data'''
  filt_cap=df['NAME_FULL_FORMATTED'].str.contains(r'^cap\b',case=False) # remove CAP samples
  filt_ioh=df['NAME_FULL_FORMATTED'].str.contains(r'^ioh\b',case=False) # also for CAP samples (new name format)
  filt_testpt=df['NAME_FULL_FORMATTED'].str.contains(r'^testpatient\b',case=False) # remove test patients
  filt_nantask=df['TASK_ASSAY'].isna()
  filt_nandttm=df[['DRAWN_DT_TM','RECEIVED_DT_TM']].isna().any(axis=1)
  df_cleaned=df.loc[~(filt_cap|filt_testpt|filt_ioh|filt_nantask|filt_nandttm)].reset_index(drop=True)
  df_cleaned['DRAWN_DT_TM']=pd.to_datetime(df_cleaned['DRAWN_DT_TM'])
  df_cleaned['RECEIVED_DT_TM']=pd.to_datetime(df_cleaned['RECEIVED_DT_TM'])
  df_cleaned['PERFORMED_DT_TM']=pd.to_datetime(df_cleaned['PERFORMED_DT_TM'])
  df_cleaned['RESULT_VAL']=df_cleaned['RESULT_VAL'].apply(lambda x: pd.to_numeric(x,errors='coerce'))
  return(df_cleaned)

def calc_encounter_baseline(row: pd.Series, df: pd.DataFrame)->pd.Series:
  '''Returns lowest previous cr for this encounter'''
  filt_date=df['PERFORMED_DT_TM']<row['PERFORMED_DT_TM']
  filt_encounter=df['ENCNTR_ID']==row['ENCNTR_ID']
  if sum(filt_date&filt_encounter):
    return(min(df.loc[filt_date&filt_encounter,'RESULT_VAL']))
  else:
    return(np.NaN)

def calc_twoday_baseline(row: pd.Series,df: pd.DataFrame)->pd.Series:
  '''Returns lowest previous cr within the past 48 hours'''
  filt_date=(df['PERFORMED_DT_TM']<row['PERFORMED_DT_TM'])&(df['PERFORMED_DT_TM']>(row['PERFORMED_DT_TM']-np.timedelta64(48,'h')))
  filt_encounter=df['ENCNTR_ID']==row['ENCNTR_ID']
  if sum(filt_date&filt_encounter):
    return(min(df.loc[filt_date&filt_encounter,'RESULT_VAL']))
  else:
    return(np.NaN)

def encode_race(race_str: str)->float:
  '''Returns 1.212 it pt race is black else 1'''
  if race_str=='Black':
    return(1.212)
  else:
    return(1.)
  
def encode_sex(sex_str: str)->float:
  '''Returns sex coefficient for mdrd - 0.72 if female, 1 if male, else None'''
  if sex_str == 'Female':
    return(0.742)
  else:
    return(1)


def calc_mdrd_baseline(row: pd.Series)->float:
    '''Returns estimated creatinine using mdrd formula if pt demographics are known, else None'''
    egfr = 75 #eGFR assumed to be 75mL/min/1.73^m2
    age=row['PT_AGE']
    race_coef=encode_race(row['PATIENT_RACE'])
    sex_coef=encode_sex(row['PATIENT_SEX'])
    if age>0:
      est_cr = (egfr/175) / (age ** -0.203) / (race_coef) / (sex_coef) # MDRD formula
      return(est_cr)
  
def stage_aki(result_val: float, baseline: float)->str:
  '''Returns stage of AKI according to KDIGO criteria'''
  if (((result_val/baseline)>3)|(result_val>4)):
    return('Stage 3')
  elif (result_val/baseline)>2:
    return('Stage 2')
  else:
    return('Stage 1')

def apply_kdigo(result_val: float,baseline: float,twoday_baseline)->str:
  '''returns stage if KDIGO criteria satisfied, else False'''
  if (result_val >= baseline*1.5)|((result_val-twoday_baseline)>0.3): 
    kdigo_stage=stage_aki(result_val,baseline)
    return(kdigo_stage)
  else:
    return(False)

def is_aki(row: pd.Series)->int:
  '''returns 1 if sample meets KDIGO aki critera, else 0'''
  if row['OUTPATIENT_BASELINE']:
    aki_ind=apply_kdigo(row['RESULT_VAL'],row['OUTPATIENT_BASELINE'],row['twoday_baseline'])
  elif row['inpatient_baseline']:
    aki_ind=apply_kdigo(row['RESULT_VAL'],row['inpatient_baseline'],row['twoday_baseline'])
  else:
    aki_ind=apply_kdigo(row['RESULT_VAL'],row['mdrd_baseline'],row['twoday_baseline'])
  return(aki_ind)
    
def aki_encounter(row: pd.Series,df:pd.DataFrame)->bool:
  """Return True if any sample from this encounter is aki else false"""
  return(df.loc[df.ENCNTR_ID==row['ENCNTR_ID'],'aki_sample'].any())

#%% main function
def main(df: pd.DataFrame)->pd.DataFrame:
  """Returns analyzed and processed data"""
  df=clean_data(df)
  df['encounter_baseline']=df.apply(calc_encounter_baseline,df=df,axis=1)
  df['twoday_baseline']=df.apply(calc_twoday_baseline,df=df,axis=1)
  df['mdrd_baseline']=df.apply(calc_mdrd_baseline,axis=1)
  df['aki_sample']=df.apply(is_aki,axis=1)
  df['aki_encounter']=df.apply(aki_encounter,df=df,axis=1)
  return(df)

if __name__=='__main__':
  df=queries.main()
  df=main(df)
  df.to_csv('prototype.csv')
  
'''
queries.py

Created by: Mark A. Zaydman
10.24.2022

Purpose: Code for querying LIS to get creatinine results for aki-reporter

Functions:
  query_oracle(sql: str) -> pd.DataFrame
  build_query() -> str

'''

import cx_Oracle
import os
import pandas as pd
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta

cx_Oracle.init_oracle_client(lib_dir=r'/opt/oracle/instantclient_21_5')


def output_type_handler(cursor, name, default_type, size, precision, scale):
	if default_type == cx_Oracle.CLOB:
		return cursor.var(cx_Oracle.LONG_STRING, arraysize=cursor.arraysize)
	if default_type == cx_Oracle.BLOB:
		return cursor.var(cx_Oracle.LONG_BINARY, arraysize=cursor.arraysize)


def query_oracle(sql: str)->pd.DataFrame:
  """Returns results of sql query LIS database"""
  host_name=os.environ.get('HOST_NAME')
  port_num=os.environ.get('PORT_NUM')
  service_name=os.environ.get('SERVICE_NAME')
  user_name=os.environ.get('USER_NAME')
  password=os.environ.get('PASSWORD')


  dsn_tns = cx_Oracle.makedsn(host_name, port_num, service_name=service_name) 
  conn = cx_Oracle.connect(user=user_name, password=password, dsn=dsn_tns) 
  conn.outputtypehandler = output_type_handler

  # conn = cx_Oracle.connect(user=os.environ.get('ORACLE_DB_USER'), password=os.environ.get('ORACLE_DB_PASS'), dsn=os.environ.get('ORACLE_DB_DSN'))
  cur = conn.cursor()
  cur.execute(sql)
  df = pd.DataFrame(cur.fetchall())
  df.columns = [x[0] for x in cur.description]
  cur.close()
  conn.close()
  return(df)

def build_query()->str:
  """Returns sql query for all cr results for encounters with new cr result in past 24 hrs plus outpatient baseline"""
  sql="""
    USER DEFINED SQL QUERY GOES HERE...
    """ 
  sql=sql.replace('\n',' ').replace('\t','')
  return(sql)

def main()->pd.DataFrame:
  """Builds, submits, and returns results of sql query"""
  sql=build_query()
  df=query_oracle(sql)
  return(df)

if __name__=='__main__':
  df=main()
  df.to_csv('%s.csv'%(datetime.today()- timedelta(days=1)).strftime('%Y-%m-%d'))
# aki-reporter

This software package contains python source code for the aki specimen capture dashboard described in Omosule et al [Insert reference]

## Usage notes

### Dependencies

- cx_oracle w/client (assuming oracle DB)
- dash
- dash_auth
- dash_bootstrap_components
- matplotlib
- numpy
- pandas
- plotly
- seaborn

### LIS Query

To deploy this package the user will have to significantly modify queries.py to develop an SQL query customized to their LIS instance.

### Scheduling

The implementation in the work of Omosule et. al. leveraged the cronjob scheduling tool on a linux server to refresh the dashboard data daily.

## Modules

### queries.py

Establishes a connection with the LIS database. The user should define a custom SQL query to retrieve all new inpatient Cr results within the past day, all Cr results for the same patient encounters, and the outpatient baseline (median Cr value over the past year).

### analytics.py

Cleans data and applies Cr based KDIGO criteria to identify and stage AKI cases.

### aki-dash.py

Provide analytical dashboard where the end user can review the aki cases, view Cr trends, and develop and inventory of specimen to capture.

### users.txt
Text file with username/password pairs for authorized users.

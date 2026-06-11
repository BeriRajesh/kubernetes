
import sys
import datetime
from calendar import monthrange

now = datetime.datetime.now()
current_month = now.month
current_year = now.year

# december 2017 has an id of 216
month_basis = 2017*12
month_basis_id = 216
# so previous months id is
month_id = ((current_year-1)*12 - month_basis + current_month) + month_basis_id - 1


#returns tuple for last month like (year, last month)
lastmonth = [(y,m+1) for y,m in (divmod((current_year*12+current_month-2), 12),)][0]
days_lastmonth = monthrange(lastmonth[0], lastmonth[1])[1]

def get_month_id():
    return month_id

def get_date():
    return "2018-01-%"
    return "{}-{}-%".format(str(lastmonth[0]).zfill(2), str(lastmonth[1]).zfill(2))

def get_date_string():
    return datetime.date(lastmonth[0], lastmonth[1], 1).strftime("%B %Y")

reports = [
    {
        'sql_string': "SELECT EXTRACT(YEAR FROM calendar_day) as year, EXTRACT(MONTH FROM calendar_day) as day, EXTRACT(DAY FROM calendar_day) as day, COUNT(*) FROM url_final_new WHERE calendar_day LIKE %s GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "url_final_new",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'enabled': True
    },
    {
        'sql_string': "SELECT EXTRACT(YEAR FROM calendar_day) as year, EXTRACT(MONTH FROM calendar_day) as day, EXTRACT(DAY FROM calendar_day) as day, COUNT(*) FROM url_final_uk_new WHERE calendar_day LIKE %s GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "url_final_uk_new",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'enabled': True
    },
    {
        'sql_string': "SELECT EXTRACT(YEAR FROM calendar_day) as year, EXTRACT(MONTH FROM calendar_day) as day, EXTRACT(DAY FROM calendar_day) as day, COUNT(*) FROM url_final_ca_new WHERE calendar_day LIKE %s GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "url_final_ca_new",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'enabled': True
    },
    {
        'sql_string': "SELECT EXTRACT(YEAR FROM timestamp) as year, EXTRACT(MONTH FROM timestamp) as day, EXTRACT(DAY FROM timestamp) as day, COUNT(*) FROM url_cn WHERE timestamp LIKE %s GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "url_cn",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'enabled': True
    },


    # {
    #     'sql_string': "SELECT EXTRACT(YEAR FROM calendar_day)as Year, EXTRACT(MONTH FROM calendar_day) as Month, EXTRACT(DAY FROM calendar_day) as Day, COUNT(*) FROM url_cn_htmltitle WHERE calendar_day LIKE %s GROUP BY 1,2,3 ORDER BY 1,2,3;",
    #     'parameters': [get_date()],
    #     'report_filename': "url_cn_htmltitle",
    #     'date_string': get_date_string(),
    #     'validations': [
    #         {'expected_rows': days_lastmonth}
    #     ],
    # },


    {
        'sql_string': "SELECT EXTRACT(YEAR FROM calendar_day)as Year, EXTRACT(MONTH FROM calendar_day) as Month, EXTRACT(DAY FROM calendar_day) as Day, COUNT(*) FROM url_agg_cn WHERE calendar_day LIKE %s  GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "url_agg_cn",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
    },



    {
        'sql_string': "SELECT EXTRACT(YEAR FROM search_date)as Year, EXTRACT(MONTH FROM search_date) as Month, EXTRACT(DAY FROM search_date) as Day, COUNT(*) FROM search_final WHERE search_date LIKE %s  GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "search_final",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
    },
    {
        'sql_string': "SELECT EXTRACT(YEAR FROM search_date)as Year, EXTRACT(MONTH FROM search_date) as Month, EXTRACT(DAY FROM search_date) as Day, COUNT(*) FROM search_final_ca WHERE search_date LIKE %s  GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "search_final_ca",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
    },
    {
        'sql_string': "SELECT EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp), EXTRACT(DAY FROM timestamp), COUNT(*) FROM search_cn WHERE timestamp LIKE %s GROUP BY 1,2,3 ORDER BY 1,2,3;",
        'parameters': [get_date()],
        'report_filename': "search_cn",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
    },





    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_final  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'report_filename': "person_demos_final",
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
    },
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_monthly  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_monthly"},
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_final_uk  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_final_uk"},
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_monthly_uk  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_monthly_uk"},
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_final_ca  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_final_ca"},
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_monthly_ca  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_monthly_ca"},
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_final_cn  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_final_cn"},
    {
        'sql_string': "SELECT month_id, COUNT(*) FROM person_demos_monthly_cn  WHERE month_id = %s GROUP BY 1 ORDER BY 1;",
        'parameters': [get_month_id()],
        'date_string': get_date_string(),
        'validations': [
            {'expected_rows': days_lastmonth}
        ],
        'report_filename': "person_demos_monthly_cn",
    }
]

def expected_rows(data, number_of_days):
    if len(data) != number_of_days:
        return '`Number of days`({}) do not match `Number of rows`({})'.format(number_of_days, len(data))

    return ''
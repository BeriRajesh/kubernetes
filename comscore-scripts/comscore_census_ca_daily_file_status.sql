/*comscore census data for CA*/
drop table if exists #temp_counts;
select top 5 visit_date, 
count(*) as record_count, 
datediff('d',TO_DATE(lag(visit_date) over(order by visit_date),'YYYYmmDD'), TO_DATE(visit_date,'YYYYmmDD')) as day_differences into #temp_counts
from comscore.comscore_census where region = 'CA'
group by 1
order by 1 desc;
select *, 
((abs(record_count - (select avg(record_count) from #temp_counts))::numeric(20,10) / record_count::numeric(20,10)) * 100.00)::numeric(20,2) as deviation_from_avg
from #temp_counts
order by visit_date desc;
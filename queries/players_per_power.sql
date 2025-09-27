with
max_power as (
	select PolarisId, max(Power) as MaxPower from (
		select distinct p1_polaris_id as PolarisId, p1_power as Power from ReplayData
		union
		select distinct p2_polaris_id as PolarisId, p2_power as Power from ReplayData
	)
	group by PolarisId
),
bucketed_power as (
	select
		*,
		(MaxPower / 25000) * 25000 as PowerBucket
	from max_power 
)
select
	concat(PowerBucket, ' - ', PowerBucket + 24999) as PowerBracket,
	count(*) as PlayerCount
from bucketed_power
group by PowerBucket
order by PowerBucket
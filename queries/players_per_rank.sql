with
max_ranks as (
	select PolarisId, max(Rank) as MaxRank from (
		select distinct p1_polaris_id as PolarisId, p1_rank as Rank from ReplayData
		union
		select distinct p2_polaris_id as PolarisId, p2_rank as Rank from ReplayData
	)
	group by PolarisId
)
select
	max(r.Name) as Rank,
	count(*) as Players
from max_ranks mr
join Ranks r on r.Id = mr.MaxRank
group by MaxRank
order by MaxRank
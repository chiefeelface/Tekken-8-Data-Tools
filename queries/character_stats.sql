with winner_loser as (
    select
        case when rd.winner = 1 then c1.Name else c2.Name end as Winner,
        case when rd.winner = 1 then c2.Name else c1.Name end as Loser
    from ReplayData rd
    join Characters c1 on c1.Id = rd.p1_chara_id
    join Characters c2 on c2.Id = rd.p2_chara_id
),
wins as (
    select Winner as Name, count(*) as Wins
    from winner_loser
    group by Winner
),
losses as (
    select Loser as Name, count(*) as Losses
    from winner_loser
    group by Loser
),
games as (
	select
		sum(w.Wins) as GlobalTotalGames,
		sum(w.Wins) / count(w.Name) as GlobalAverageGames
	from wins w
	full outer join losses l on w.Name = l.Name
),
stats as (
	select
	    coalesce(w.Name, l.Name, 'Unknown') as Character,
	    coalesce(w.Wins, 0) as Wins,
	    coalesce(l.Losses, 0) as Losses,
	    coalesce(w.Wins, 0) + coalesce(l.Losses, 0) as TotalGames,
	    coalesce(w.Wins, 0) / cast(coalesce(w.Wins, 0) + coalesce(l.Losses, 0) as float) as RawWinRate,
	    -- Multiplying by 2 puts more emphasis on games played, probably too much though
	    coalesce(w.Wins + g.GlobalAverageGames * wr.GlobalAverageWinRate * 2, 0) / (coalesce(w.Wins, 0) + coalesce(l.Losses, 0) + g.GlobalAverageGames * 2) as BayesianWinRate
    from wins w
	full outer join losses l on w.Name = l.Name
	cross join games g
	cross join (
		select
			avg(RawWinRate) as GlobalAverageWinRate
		from (
			select
				coalesce(w.Name, l.Name, 'Unknown') as Character,
				coalesce(w.Wins, 0) / cast(coalesce(w.Wins, 0) + coalesce(l.Losses, 0) as float) as RawWinRate
			from wins W
			full outer join losses l on w.Name = l.Name
		)
	) wr
)
select * from stats
order by RawWinRate
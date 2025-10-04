WITH winner_loser AS (
    SELECT
        CASE WHEN rd.winner = 1 THEN c1.Name ELSE c2.Name END AS Winner,
        CASE WHEN rd.winner = 1 THEN c2.Name ELSE c1.Name END AS Loser
    FROM ReplayData rd
    JOIN Characters c1 ON c1.Id = rd.p1_chara_id
    JOIN Characters c2 ON c2.Id = rd.p2_chara_id
),

wins AS (
    SELECT Winner AS Name, COUNT(*) AS Wins
    FROM winner_loser
    GROUP BY Winner
),

losses AS (
    SELECT Loser AS Name, COUNT(*) AS Losses
    FROM winner_loser
    GROUP BY Loser
),

-- Replace full outer join between wins and losses with UNION of two LEFT JOINs
win_loss_union AS (
    SELECT
        w.Name AS Name,
        w.Wins,
        l.Losses
    FROM wins w
    LEFT JOIN losses l ON w.Name = l.Name

    UNION

    SELECT
        l.Name AS Name,
        w.Wins,
        l.Losses
    FROM losses l
    LEFT JOIN wins w ON w.Name = l.Name
),

games AS (
    SELECT
        SUM(COALESCE(Wins, 0)) AS GlobalTotalGames,
        SUM(COALESCE(Wins, 0)) * 1.0 / COUNT(Name) AS GlobalAverageGames
    FROM win_loss_union
),

-- Calculate raw win rates for all characters
raw_rates AS (
    SELECT
        Name,
        COALESCE(Wins, 0) AS Wins,
        COALESCE(Losses, 0) AS Losses,
        COALESCE(Wins, 0) + COALESCE(Losses, 0) AS TotalGames,
        COALESCE(Wins * 1.0 / NULLIF(Wins + Losses, 0), 0) AS RawWinRate
    FROM win_loss_union
),

-- Compute the global average win rate
global_avg_winrate AS (
    SELECT AVG(RawWinRate) AS GlobalAverageWinRate FROM raw_rates
),

-- Final stats with BayesianWinRate
stats AS (
    SELECT
        r.Name AS Character,
        r.Wins,
        r.Losses,
        r.TotalGames,
        r.RawWinRate
        -- Bayesian formula using cross join to bring in global values
        --(COALESCE(r.Wins, 0) + g.GlobalAverageGames * a.GlobalAverageWinRate * 2.0) / (r.TotalGames + g.GlobalAverageGames * 2.0) AS BayesianWinRate
    FROM raw_rates r
    CROSS JOIN games g
    CROSS JOIN global_avg_winrate a
)

SELECT * FROM stats
ORDER BY RawWinRate DESC;
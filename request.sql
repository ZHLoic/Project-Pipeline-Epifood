SELECT
  plat.code,
  plat.libelle,
  plat.total,
  t.ingestion_time
FROM croustillant_db.plats_top t
CROSS JOIN UNNEST(t.data) AS u(plat)
LIMIT 20;

import duckdb
from pathlib import Path
R=Path(__file__).resolve().parents[1]; con=duckdb.connect(str(R/"finiq_stage2.duckdb"))
files=["instructions","swift","nostro","workflow","gl"]
for f in files: con.execute(f"CREATE OR REPLACE TABLE r_{f} AS SELECT *,'{f.upper()}' source_system FROM read_csv_auto(?)",[str(R/f"data/raw/{f}.csv")])
u=" UNION ALL ".join([f"SELECT * FROM r_{f}" for f in files])
con.execute(f"CREATE OR REPLACE TABLE events AS SELECT 'JRN-'||customer_ref journey_id,* FROM ({u})")
con.execute("CREATE OR REPLACE TABLE rules AS SELECT * FROM read_csv_auto(?)",[str(R/"config/expectations.csv")])
con.execute("""CREATE OR REPLACE TABLE expectations AS WITH b AS (
SELECT e.journey_id,e.event_code from_event,e.event_time from_time,r.expected_event,r.window_minutes,
(SELECT min(x.event_time) FROM events x WHERE x.journey_id=e.journey_id AND x.event_code=r.expected_event AND x.event_time>=e.event_time) observed_time
FROM events e JOIN rules r ON e.event_code=r.from_event)
SELECT *,from_time+window_minutes*INTERVAL '1 minute' deadline,
CASE WHEN observed_time IS NULL OR observed_time>from_time+window_minutes*INTERVAL '1 minute' THEN 'TRIGGERED' ELSE 'SATISFIED' END status FROM b""")
con.execute("""CREATE OR REPLACE TABLE direct_suspense AS SELECT s.journey_id,s.event_time suspense_time,
(SELECT max(x.event_time) FROM events x WHERE x.journey_id=s.journey_id AND x.event_time<s.event_time) last_observed
FROM events s WHERE s.event_code='SUSPENSE_POSTED' AND NOT EXISTS
(SELECT 1 FROM expectations q WHERE q.journey_id=s.journey_id AND q.status='TRIGGERED' AND q.deadline<s.event_time)""")
con.execute("""CREATE OR REPLACE VIEW summary AS SELECT e.journey_id,min(e.event_time) start_time,max(e.event_time) last_event,max(e.amount) amount,any_value(e.currency) currency,
CASE WHEN d.journey_id IS NOT NULL THEN 'DIRECT_TO_SUSPENSE'
WHEN (SELECT count(*) FROM expectations q WHERE q.journey_id=e.journey_id AND q.status='TRIGGERED')>1 THEN 'MULTI_TRIGGER'
WHEN (SELECT count(*) FROM expectations q WHERE q.journey_id=e.journey_id AND q.status='TRIGGERED')=1 THEN 'TRIGGERED' ELSE 'NORMAL' END derived_state
FROM events e LEFT JOIN direct_suspense d ON e.journey_id=d.journey_id GROUP BY e.journey_id,d.journey_id""")
print(con.execute("SELECT derived_state,count(*) FROM summary GROUP BY 1").fetchall()); con.close()

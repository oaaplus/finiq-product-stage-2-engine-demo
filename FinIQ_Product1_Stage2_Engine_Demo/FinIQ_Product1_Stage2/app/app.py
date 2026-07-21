import streamlit as st,duckdb,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]; DB=R/"finiq_stage2.duckdb"
if not DB.exists(): subprocess.run([sys.executable,str(R/"engine/build_engine.py")],check=True)
c=duckdb.connect(str(DB),read_only=True); s=c.execute("SELECT * FROM summary ORDER BY last_event DESC").df()
st.set_page_config(page_title="FinIQ Product 1 Engine Demo",layout="wide")
st.title("FinIQ Product 1 — Cross-Border Transaction Journey Visibility")
st.caption("ENGINE-DRIVEN PROTOTYPE • states derived from fragmented raw source records")
p=st.sidebar.radio("Navigation",["Control Room","Journey Explorer","Expected Actions & Triggers","Direct-to-Suspense"])
a,b,d,e=st.columns(4); a.metric("Journeys",len(s)); b.metric("Normal",(s.derived_state=="NORMAL").sum()); d.metric("Triggered",s.derived_state.isin(["TRIGGERED","MULTI_TRIGGER"]).sum()); e.metric("Direct-to-Suspense",(s.derived_state=="DIRECT_TO_SUSPENSE").sum())
if p=="Control Room":
 st.dataframe(s,use_container_width=True,hide_index=True); st.info("Raw files contain no journey-state or trigger labels. These states were derived by the engine.")
elif p=="Journey Explorer":
 j=st.selectbox("Journey",s.journey_id.tolist()); st.subheader("Reconstructed Evidence Timeline")
 st.dataframe(c.execute("SELECT event_time,event_code,source_system,source_ref,amount,currency FROM events WHERE journey_id=? ORDER BY event_time",[j]).df(),use_container_width=True,hide_index=True)
 st.subheader("Expected Next Actions")
 st.dataframe(c.execute("SELECT from_event,from_time,expected_event,deadline,observed_time,status FROM expectations WHERE journey_id=? ORDER BY from_time",[j]).df(),use_container_width=True,hide_index=True)
elif p=="Expected Actions & Triggers":
 st.subheader("Engine-Detected Missed Expectations")
 st.dataframe(c.execute("SELECT journey_id,from_event,expected_event,deadline,observed_time,status FROM expectations WHERE status='TRIGGERED' ORDER BY deadline DESC").df(),use_container_width=True,hide_index=True)
 st.caption("Windows are synthetic test parameters, not asserted Nigerian bank SLAs.")
else:
 ds=c.execute("SELECT d.*,s.amount,s.currency FROM direct_suspense d JOIN summary s USING(journey_id) ORDER BY suspense_time DESC").df()
 st.subheader("Engine-Detected Direct-to-Suspense"); st.dataframe(ds,use_container_width=True,hide_index=True)
 j=st.selectbox("Inspect evidence",ds.journey_id.tolist())
 st.dataframe(c.execute("SELECT event_time,event_code,source_system,source_ref FROM events WHERE journey_id=? ORDER BY event_time",[j]).df(),use_container_width=True,hide_index=True)
 st.error("Suspense observed without a prior engine-detected missed expectation. Pre-suspense evidence context preserved.")
st.divider(); st.caption("Synthetic/reference environment • Product 2 out of scope • proprietary methodology suppressed")

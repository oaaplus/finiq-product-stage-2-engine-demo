import streamlit as st,pandas as pd
from pathlib import Path
df=pd.read_csv(Path(__file__).parent/"data/raw_events.csv",parse_dates=["event_time"]);df["journey_id"]="JRN-"+df.customer_ref
rules={"INSTRUCTION_RECEIVED":("VALIDATED",30),"VALIDATED":("SWIFT_SENT",60),"SWIFT_SENT":("SETTLEMENT_OBSERVED",360),"SETTLEMENT_OBSERVED":("BENEFICIARY_CONFIRMED",180),"BENEFICIARY_CONFIRMED":("CLOSED",120)}
out=[]
for jid,g in df.groupby("journey_id"):
 for _,r in g.iterrows():
  if r.event_code in rules:
   nxt,m=rules[r.event_code]; dl=r.event_time+pd.Timedelta(minutes=m); c=g[(g.event_code==nxt)&(g.event_time>=r.event_time)]; obs=c.event_time.min() if len(c) else pd.NaT
   out.append([jid,r.event_code,nxt,dl,obs,"TRIGGERED" if pd.isna(obs) or obs>dl else "SATISFIED"])
ex=pd.DataFrame(out,columns=["journey_id","from_event","expected_event","deadline","observed_time","status"])
direct=[];summary=[]
for jid,g in df.groupby("journey_id"):
 sp=g[g.event_code=="SUSPENSE_POSTED"]; isdirect=False
 if len(sp):
  stime=sp.event_time.min(); isdirect=ex[(ex.journey_id==jid)&(ex.status=="TRIGGERED")&(ex.deadline<stime)].empty
 if isdirect: direct.append(jid)
 n=len(ex[(ex.journey_id==jid)&(ex.status=="TRIGGERED")])
 state="DIRECT_TO_SUSPENSE" if isdirect else ("MULTI_TRIGGER" if n>1 else ("TRIGGERED" if n else "NORMAL"))
 summary.append([jid,g.event_time.min(),g.event_time.max(),g.amount.max(),g.currency.iloc[0],state])
s=pd.DataFrame(summary,columns=["journey_id","start","last_event","amount","currency","derived_state"])
st.set_page_config(page_title="FinIQ Product 1",layout="wide");st.title("FinIQ Product 1 — Cross-Border Transaction Journey Visibility");st.caption("ENGINE-DRIVEN DEMO • states derived from raw synthetic source records")
p=st.sidebar.radio("Navigation",["Control Room","Journey Explorer","Expected Actions & Triggers","Direct-to-Suspense"])
a,b,c,d=st.columns(4);a.metric("Journeys",len(s));b.metric("Normal",(s.derived_state=="NORMAL").sum());c.metric("Triggered",s.derived_state.str.contains("TRIGGER").sum());d.metric("Direct-to-Suspense",len(direct))
if p=="Control Room": st.dataframe(s,use_container_width=True,hide_index=True);st.info("Raw records contain no journey-state labels. States are calculated by the demo engine.")
elif p=="Journey Explorer":
 j=st.selectbox("Journey",s.journey_id.tolist());st.subheader("Reconstructed Evidence Timeline");st.dataframe(df[df.journey_id==j].sort_values("event_time"),use_container_width=True,hide_index=True);st.subheader("Derived Expectations");st.dataframe(ex[ex.journey_id==j],use_container_width=True,hide_index=True)
elif p=="Expected Actions & Triggers": st.subheader("Engine-Detected Missed Expectations");st.dataframe(ex[ex.status=="TRIGGERED"],use_container_width=True,hide_index=True);st.caption("Timing windows are synthetic test parameters, not bank SLAs.")
else:
 ds=s[s.journey_id.isin(direct)];st.subheader("Direct-to-Suspense");st.dataframe(ds,use_container_width=True,hide_index=True)
 if len(ds):
  j=st.selectbox("Inspect evidence",ds.journey_id.tolist());st.dataframe(df[df.journey_id==j].sort_values("event_time"),use_container_width=True,hide_index=True);st.error("Suspense observed without a prior detected missed expectation. Evidence trail preserved.")
st.caption("Product 2 out of scope • proprietary methodology suppressed")

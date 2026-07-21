# FinIQ Product 1 Stage 2 — Engine-Driven Demo
Raw source-like files contain no pre-labelled journey states or triggers. DuckDB reconstructs journeys, evaluates configurable expected-next-action windows, derives missed expectations, and detects direct-to-suspense. Streamlit displays derived outputs.

Run:
pip install -r requirements.txt
python engine/build_engine.py
streamlit run app/app.py

Prototype limitation: correlation uses a clean shared synthetic reference. Production requires scored multi-field correlation and ambiguity handling. Timing windows are synthetic test parameters, not Nigerian bank SLAs. Product 2 is out of scope.

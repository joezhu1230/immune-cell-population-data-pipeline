setup:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

pipeline:
	python load_data.py
	python run_pipeline.py

dashboard:
	streamlit run app.py --server.headless true --server.port 8501

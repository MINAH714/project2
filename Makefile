.PHONY: all

all:
	uvicorn main5:app --reload --port 8080
	streamlit run client5.py
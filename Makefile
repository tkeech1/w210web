fastapi:
	uvicorn src.main:app --reload 
	#--log-config=config/log_conf.yaml

build-docker:
	docker build -f Dockerfile -t fastapi:latest .

run-docker:
	docker run -it -p 8000:8000 fastapi:latest
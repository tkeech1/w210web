fastapi:
	uvicorn src.main:app --reload 
	#--log-config=config/log_conf.yaml

build-docker:
	docker build -f Dockerfile -t fastapi:latest .

run-docker:
	docker run -d -p 8000:8000 fastapi:latest

transfer-data:
	scp data/*.parquet ec2-52-91-62-139.compute-1.amazonaws.com:/home/ec2-user/w210web/data
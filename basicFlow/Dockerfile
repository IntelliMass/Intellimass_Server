FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt  ./
RUN  pip3 install -r requirements.txt

COPY ["lambdaWrapper.py", "main.py", "Step1.py", "Step2.py", "Step3.py", "Step4.py", "Step5.py", "config.py", "./"]

CMD ["lambdaWrapper.lambda_handler"]
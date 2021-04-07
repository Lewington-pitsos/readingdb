FROM public.ecr.aws/lambda/python:3.8

# Copy function code and package.json
ADD readingdb ./readingdb

COPY readingdb/lamb.py ./
COPY requirements.txt ./
COPY aws/credentials ./

# Install NPM dependencies for function
RUN pip install -r requirements.txt

ENV AWS_SHARED_CREDENTIALS_FILE=credentials

# Set the CMD to your handler
CMD [ "lamb.handler" ]
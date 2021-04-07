FROM public.ecr.aws/lambda/python:3.8

# Copy function code and package.json
ADD readingdb ./readingdb

COPY lamb.py ./
COPY requirements.txt ./

# Install NPM dependencies for function
RUN pip install -r requirements.txt

ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=

# Set the CMD to your handler
CMD [ "lamb.handler" ]
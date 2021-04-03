FROM public.ecr.aws/lambda/python:3.8

# Copy function code and package.json
ADD readingdb ./readingdb

COPY lamb.py ./
COPY requirements.txt ./

# Install NPM dependencies for function
RUN pip install -r requirements.txt

# Set the CMD to your handler
CMD [ "lamb.handler" ]
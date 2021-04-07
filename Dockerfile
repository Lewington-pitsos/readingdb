FROM public.ecr.aws/lambda/python:3.8

# Copy function code and package.json
ADD readingdb ./readingdb

COPY lamb.py ./
COPY requirements.txt ./

# Install NPM dependencies for function
RUN pip install -r requirements.txt

ENV AWS_ACCESS_KEY_ID=AKIA52XQLVT4QKU7LEPX
ENV AWS_SECRET_ACCESS_KEY=QfQ7cendKQuOdLHbaa94y1I4b0yeM08Z0H5TfuM5

# Set the CMD to your handler
CMD [ "lamb.handler" ]
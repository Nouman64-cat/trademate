# syntax=docker/dockerfile:1
# Use the official AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt to the root of the task
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages using a cache mount to speed up re-builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy the entire app directory to the task root
COPY app/ ${LAMBDA_TASK_ROOT}/app/

# Set the CMD to your handler
CMD [ "app.services.research_handler.lambda_handler" ]

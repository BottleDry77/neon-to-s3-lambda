FROM public.ecr.aws/lambda/python:3.9

# Install PostgreSQL client tools
RUN yum install -y \
    postgresql \
    postgresql-libs \
    postgresql-server \
    && yum clean all

# Copy function code
COPY lambda_function.py requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Set the CMD to our function handler
CMD ["lambda_function.lambda_handler"]

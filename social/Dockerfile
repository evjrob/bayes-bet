FROM public.ecr.aws/lambda/python:3.11 AS browser

RUN yum install -y unzip

# Install Chromium
ENV CHROMIUM_VERSION=1002910
COPY install-browser.sh /tmp/
RUN /usr/bin/bash /tmp/install-browser.sh


FROM public.ecr.aws/lambda/python:3.11 as base

COPY chrome-deps.txt /tmp/
RUN yum install -y $(cat /tmp/chrome-deps.txt)
COPY --from=browser /opt/chrome /opt/chrome
COPY --from=browser /opt/chromedriver /opt/chromedriver

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]

#!/bin/bash

celery -A tasks worker --app=hereboxweb.tasks --loglevel=info
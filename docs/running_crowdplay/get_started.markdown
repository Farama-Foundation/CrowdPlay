---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Quickstart
nav_order: 1
layout: default
parent: Running CrowdPlay
---

## Getting Started with CrowdPlay

### 1. Prerequisites

Install and start Docker. Clone this repository.

### 2. (Optional) Download ROMs

If you wish to run Atari environments, download the ROMs using the following commands:

```bash
pip install 'AutoROM>=0.4.2'
AutoROM -d backend/ROM
```

This will download the ROMs for you, which will then be copied into the Docker container automatically. You can skip this step if you do not plan to use Atari environments.

### 3. Running the app

Run `docker-compose -f docker-compose.dev.yaml up` to start the project. If you have previously run the project and would like to update all underlying packages, run the following:

```bash
docker-compose -f docker-compose.dev.yaml down && rm -r data && docker-compose -f docker-compose.dev.yaml build && docker-compose -f docker-compose.dev.yaml up -d
```

Afterwards, go to <http://127.0.0.1:9000> to start the app.

## Deployment

You can deploy this locally or on your own server by running `docker-compose -f docker-compose.dev.yaml up`. For more robust deployment, see [Deployment on Elastic Beanstalk](deploy_on_aws.markdown).

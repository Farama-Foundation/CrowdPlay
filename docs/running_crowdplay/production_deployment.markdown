---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Production Deployment
nav_order: 7
layout: default
parent: Running CrowdPlay
---

## Deploying CrowdPlay for Production

CrowdPlay offers several ways to deploy your application. [A quick way to deploy CrowdPlay scalably is using Amazon Elastic Beanstalk.](deploy_on_aws.markdown) For deployment on your own infrastructure, read on.

### Deployment with Local MySQL Database

The `docker-compose.localdb.yaml` file provides a fully self-contained CrowdPlay deployment including a MySQL database. To start it, run the following command:

```bash
MYSQL_ROOT_PASSWORD="changeme" MYSQL_PASSWORD="changemetoo" docker-compose -f docker-compose.localdb.yaml up -d         
```

This will start a full CrowdPlay deployment on the local machine running on part 80. You should change the passwords in the command above. The MySQL database will be persistent between restarts and by default is saved into the `data` directory. You might want to change this location by editing the `docker-compose.localdb.yaml` file.

### Deployment with Remote MySQL Database

In order to run a CrowdPlay deployment with your own MySQL instance, you can instead use the `docker-compose.yaml` file. You will need to set `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` and `MYSQL_DATABASE` in your environment. The `storage/crowdplaydb.sql` file contains the database schema; you can use this file to create the CrowdPlay database in your MySQL instance.

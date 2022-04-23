---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Creating your own dataset
nav_order: 9
parent: CrowdPlay Atari Dataset
layout: default
---

## Creating your own Dataset

CrowdPlay comes with a script to automatically and incrementally download trajectories and metadata from a running CrowdPlay platform instance into a local dataset package. All you need to do is specify the URI of the MySQL database the running instance is using. For a local instance you can run the following command inside the `dump_db` folder:

```bash
DATABASE_URI=mysql+pymysql://root:rootpassword@localhost:3306/crowdplaydb python3 dump_db.py
```

For a production instance, change the MySQL hostname, username and password accordingly. You need to have both the dataset as well as the backend package installed into local Python environment to run this script.

Download is cumulative, i.e. if you already have a local dataset, this will add to it. If you would like to create a new dataset, delete the `dataset/data` folder before running `dump_db`.

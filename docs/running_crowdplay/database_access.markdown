---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Integration with recruitment channels
nav_order: 12
parent: Running CrowdPlay
layout: default
---

## Database access and integration with MTurk and other recruitment channels

CrowdPlay can automatically capture worker and HIT IDs from MTurk workers and other information from other recruitment channels. These are saved to the database, for downstream processing such as payments and bonus payments to workers.

### Capturing user details

#### MTurk

For MTurk workers, user details can be captured automatically through URL parameters such as `?assignmentId={assignmentId}&hitId={hitId}&workerId={workerId}`. A small script can be put into your MTurk HIT description to generate a worker-specific link automatically:

```html
<a id="app-link" target="_blank"> Click here to play! </a>
<script>
    var aElem = document.getElementById('app-link')
    var urlParams = new URLSearchParams(window.location.search);
    var assignmentId = urlParams.get('assignmentId') || '';
    var hitId = urlParams.get('hitId') || '';
    var workerId = urlParams.get('workerId') || '';
    var urlApp = 'http://ataricrowdsourcing-env-mt0818.eba-ukmsjbpa.us-east-1.elasticbeanstalk.com/?f=mturk&t=montezuma_revenge_mturk&assignmentId={assignmentId}&hitId={hitId}&workerId={workerId}';
    urlApp = urlApp.replace('{assignmentId}', assignmentId)
    urlApp = urlApp.replace('{hitId}', hitId)
    urlApp = urlApp.replace('{workerId}', workerId)
    aElem.href = urlApp
</script>
```

#### Other channels

Where a customized link isn't possible (for instance in an email or social media campaign meant to be resahred), but individual user details are still required (e.g. for downstream payment processing), users can be asked to enter details manually when entering the app. We provide an example for this asking for email addresses, when entering the app through a link with a `?f=email` parameter. See also [Customizing the UI](../customizing_crowdplay/custom_ui.markdown) for more details.

#### Problem reports

Finally, CrowdPlay allows users to submit bug reports, which are saved to the database.

### Accessing user details

Currently, all of these details can be accessed directly through MySQL. In order to do this, connect to the database using MySQL Workbench or your favourite MySQL client. For instances deployed on Amazon EB, use the connection details you noted down when you [set up the deployment](./deploy_on_aws.markdown). If you are running the `docker-compose.dev` deployment locally for testing and would like to check out the database, you can connect to it on `mysql://crowdplayuser:userpassword@localhost:3306/crowdplaydb`. For other deployments, use the appropriate connection details.

Once connected, you can see MTurk details in the `sessions` table: The `assignment_id`, `worker_id` and `hit_id` columns give the respective details from MTurk. The `token` column gives a randomly generated token that workers could be asked to paste into the MTurk website to submit their assignment for payment (this token will only be shown to them if they complete their assignment, subject to [requirements defined in the backend's `environments.py` file](../customizing_crowdplay/custom_environments.markdown)). Furthermore, the `completed` and `bonus` columns show the fraction of task requirements the worker has fulfilled, and the amount of bonus payment, both computed from the environment callables by the backend.

Any other user details such as email addresses or bug reports are stored in the `user_data` table in key-value format, and can be matched to details in the `sessions` table by matching the `visit_id` column. For instance, to display all collected email addresses, together with all the details from the `sessions` table, you can run:

```sql
SELECT * FROM crowdplaydb.user_data INNER JOIN crowdplaydb.sessions ON crowdplaydb.sessions.visit_id = crowdplaydb.user_data.visit_id WHERE crowdplaydb.user_data.key_string = 'email' ORDER BY info_id DESC;
```

For a future version of CrowdPlay, we plan to provide scripts that can automatically submit payment information to MTurk based on information in the database.

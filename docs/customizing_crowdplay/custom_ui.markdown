---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Customizing the UI
nav_order: 7
layout: default
parent: Customizing CrowdPlay
---

## UI configuration

You will likely want to add your own consent form to the frontend. To do this, edit `frontend/src/SessionSetup/ConsentModal.js` and add your own text. You can use HTML tags as needed.

Additionally we offer the option to collect information from the user prior to starting. We provide an example of this in `frontend/src/SessionSetup/useStartModal.js`, where we ask users to provide their email address to participate in a raffle. You could change this to collect any other information you would like.

This, and some other UI elements, are shown only to some users but not others, e.g. you would not want to ask MTurk users for their email address. This is controlled through `sessionSetupDetails.user_type` in the frontend code, which is set by a URL parameter `from` or `f`. For instance, entering the app through <http://127.0.0.1:9000/?f=email> will show the email prompt, while entering through <http://127.0.0.1:9000/?from=mturk> will not (but will instead show a UI element to get a token after task completion, and will show estimated bonus payments).

Currently, the UI will change for the following user types:

* For `mturk`, users will be shown real-time payment information if provided by the environment. Upon completing their task, users will be shown a token that they can paste into the MTurk website to submit their assignment for payment.
* For `email`, users will be asked to provide their email address before starting the game, which can be used to contact them about payment or other follow-up information later.
* Any other user type will be shown the default user type. It can still be useful to pass different `/?f=...` parameters to the URL, for instance to track where users have been recruited from - the `/?f=...` parameter is saved as-is to the MySQL database.

It would be possible to further customize the UI for other user types, in a similar manner to the above.

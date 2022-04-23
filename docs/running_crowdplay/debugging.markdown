---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Debugging in VS Code
nav_order: 4
layout: default
parent: Running CrowdPlay
---

## Debugging in VS Code

It's possible to debug the CrowdPlay backend Python code while running inside a dockerized deployment. For this, you need Visual Studio Code with the Python and Docker plugins. Run `docker-compose -f docker-compose.vscode.yml up -d --build`, or right-click on the `docker-compose.vscode.yml` in VS Code and select `Compose Up`.

Then, in the VS Code Debug menu, select `Add Configuration...` and add the following to your `launch.json` file under configurations:

``` json
        {
            "name": "Python: Remote Attach",
            "type": "python",
            "request": "attach",
            "port": 5678,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/backend",
                    "remoteRoot": "/usr/src/crowdplay"
                }
            ]
        }
```

Finally, select `Python: Remote Attach` in the debug menu and click the green triangle. Note that when using the `docker-compose.vscode.yml` file, the backend will not run unless a debugger is connected - this is normal behavior. If you find the backend unresponsive, check that the debugger is connected.

Most code changes you make on both the frontend and backend will be automatically synced to the Docker containers, without needing to restart them. There are two exceptions:

1. Any changes to required (Python, npm or system) packages will require the containers to be rebuilt. You can do this by right-clicking the `docker-compose.vscode.yml` file in VS code and selecting `Compose Restart`.
2. Some code errors can cause the respective main process in either Docker container to crash. This is mostly an issue with syntax errors in the backend. If this happens, the respective container needs to be restarted, but a full rebuild is usually not necessary. It is easiest to do this in the Docker Desktop dashboard.

---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Support and Contributing
nav_order: 100
layout: default
has_children: false
---

## Support

We hope that CrowdPlay will be useful to the wider community, and welcome any feedback, suggestions, or contributions. We encourage you to open [issues](https://github.com/mgerstgrasser/crowdplay/issues) and [pull requests](https://github.com/mgerstgrasser/crowdplay/pulls) on Github, and to [contact us](mailto:matthias@seas.harvard.edu) if you have any questions or comments.

## Contributing

We also encourage you to contribute back any improvements and extensions you make to CrowdPlay. Follow the directons under [Debugging in VS Code](../running_crowdplay/debugging.markdown) to set up a local environment for development.

We use [black](https://github.com/psf/black) and [flake8](https://flake8.pycqa.org/en/latest/) to format and lint the backend, and [ESLint](https://eslint.org/) to lint the frontend. We provide a pre-commit hook that can run and optionally enforce these conventions locally. To enable this, run `pip install pre-commit`. You can then run `pre-commit run --all-files` to manually format and lint all files, or you can run `pre-commit install` to have git automatically format and lint all files before committing.

---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: CrowdPlay
nav_order: 1
layout: default
---

## CrowdPlay: Crowdsourcing Human Demonstrations for Offline Learning

[Matthias Gerstgrasser](https://matthias.gerstgrasser.net/), Rakshit Trivedi, [David C. Parkes](https://parkes.seas.harvard.edu/)

[Paper](https://openreview.net/pdf?id=qyTBxTztIpQ){: .btn  .mr-4}
[Code](https://github.com/mgerstgrasser/crowdplay){: .btn  .mr-4}
[Quickstart](running_crowdplay/get_started.markdown){: .btn  .mr-4}
[Dataset](crowdplay_atari_dataset/crowdplay_atari.markdown){: .btn  .mr-4}

![A screenshot of CrowdPlay in action](images/screenshot.png){:style="display:block; margin-left:auto; margin-right:auto; width:250px"}

CrowdPlay is a platform for crowdsourcing human demonstration trajectories at scale in RL environments. It interfaces with standard RL simulators that implement an OpenAI Gym-style API consisting of a `reset` and a `step` function. CrowdPlay can be used to generate large-scale datasets of human demonstrations with minimal effort, as detailed in our publication [CrowdPlay: Crowdsourcing Human Demonstrations for Offline Learning](https://openreview.net/forum?id=qyTBxTztIpQ) *Matthias Gerstgrasser, Rakshit Trivedi, David C. Parkes*

If you use our platform or dataset in your publication, we ask that you cite it using this bibtex entry:

```bibtex
@inproceedings{
gerstgrasser2022crowdplay,
title={CrowdPlay: Crowdsourcing Human Demonstrations for Offline Learning},
author={Matthias Gerstgrasser and Rakshit Trivedi and David C. Parkes},
booktitle={International Conference on Learning Representations},
year={2022},
url={https://openreview.net/forum?id=qyTBxTztIpQ}
}
```

## Acknowledgements

We thank Francisco Ramos for his help in implementing the CrowdPlay software, especially on the frontend. We would like to thank anonymous reviewers at ICLR 2022 for their constructive feedback and discussions. This research is funded in part by Defense Advanced Research Projects Agency under Cooperative Agreement HR00111920029. The content of the information does not necessarily reflect the position or the policy of the Government, and no official endorsement should be inferred. This is approved for public release; distribution is unlimited.

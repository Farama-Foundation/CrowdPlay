# CrowdPlay: Crowdsourcing Human Demonstrations for Offline Learning

Matthias Gerstgrasser, Rakshit Trivedi, David Parkes

* [Paper](https://openreview.net/pdf?id=qyTBxTztIpQ)
* [Code](https://github.com/mgerstgrasser/crowdplay)
* [Dataset](https://mgerstgrasser.github.io/crowdplay/crowdplay_atari_dataset/crowdplay_atari.html)
* [Documentation](https://mgerstgrasser.github.io/crowdplay)

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

## Quick Start

### 1. Prerequisites

Install and start Docker. Clone this repository.

### 2. Running the app

Run `docker-compose -f docker-compose.dev.yaml up` to start the project. If you have previously run the project and would like to update all underlying packages, run the following:

```bash
docker-compose -f docker-compose.dev.yaml down && rm -r data && docker-compose -f docker-compose.dev.yaml build && docker-compose -f docker-compose.dev.yaml up -d
```

Afterwards, go to <http://127.0.0.1:9000> to start the app. Also check out the [documentation](https://mgerstgrasser.github.io/crowdplay/).

## Acknowledgements

We thank Francisco Ramos for his help in implementing the CrowdPlay software, especially on the frontend. We would like to thank anonymous reviewers at ICLR 2022 for their constructive feedback and discussions. This research is funded in part by Defense Advanced Research Projects Agency under Cooperative Agreement HR00111920029. The content of the information does not necessarily reflect the position or the policy of the Government, and no official endorsement should be inferred. This is approved for public release; distribution is unlimited.

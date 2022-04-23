export const SpaceTypes = {
  DISCRETE: 'Discrete',
  BOX: 'Box',
  MULTI_BINARY: 'MultiBinary',
  MULTI_DISCRETE: 'MultiDiscrete',
  DICT: 'Dict',
}

// TODO: how about using a state machine for this?
// export const EnvState = {
//   WAITING: 0,
//   READY: 1,
//   STARTING: 2,
//   STARTED: 3,
//   ENDED: 4,
//   FAULT: 5,
// }

export const EnvState = {
  NOTREADY: 0,
  READY: 1,
  COUNTDOWN: 2,
  COUNTDOWN_DONE: 3,
  STARTING: 4,
  STARTED: 5,
  EPISODE_ENDED: 6,
  INSTANCE_ENDED: 7,
  FAULT: 8,
}

export const actionMeaning = {
  0: 'NOOP',
  1: 'FIRE',
  2: 'RIGHT',
  3: 'LEFT',
  4: 'RIGHT + FIRE',
  5: 'LEFFT + FIRE',
}

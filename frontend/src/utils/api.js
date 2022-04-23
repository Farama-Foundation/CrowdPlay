import debug from 'debug'
import { obj2qs } from './utils'

const log = debug('atari:api')

const apiV1 = '/api/v1'
export const endpoints = {
  // listEnvsId: `${apiV1}/list-envs-id`,
  make: envId => `${apiV1}/make/${envId}`,
  close: instanceId => `${apiV1}/close/${instanceId}`,
  start: instanceId => `${apiV1}/start/${instanceId}`,
  // listEnvs: `${apiV1}/list-envs`,
  // listEnvsWithGames: worker_id => (
  //   `${apiV1}/list-envs-with-games${worker_id ? `?worker_id=${worker_id}` : ''}`
  // ),
  // listHitsWithTurks: token => (
  //   `${apiV1}/list-hits-with-turks${token ? `?token=${token}` : ''}`
  // ),
  // listSteps: gameId => `${apiV1}/list-steps/${gameId}`,
  // stepImage: (gameId, stepIter, agentKey) => (
  //   `${apiV1}/step-image/${gameId}/${stepIter}?agent_key=${encodeURIComponent(agentKey)}`
  // ),
  // downloadGame: gameId => `${apiV1}/download-game/${gameId}`,
  // downloadInstance: instanceId => `${apiV1}/download-instance/${instanceId}`,
  sessionSetup: `${apiV1}/hello`,
  sessionToken: visit_id => `${apiV1}/session/${visit_id}/token`,

  collectUserData: `${apiV1}/collect-user-data`,
  get_scores: visit_id => `${apiV1}/get_scores/${visit_id}`,
  get_task_choices: `${apiV1}/get_task_choices`,
}

const applicationJson = { 'Content-Type': 'application/json' }
const reqOptions = { headers: applicationJson }
const postOptions = { ...reqOptions, method: 'POST' }

// export async function listEnvsId() {
//   log('Listing environments...')

//   const resp = await fetch(endpoints.listEnvsId, reqOptions)
//   const data = await resp.json()

//   log('Environments loaded:', data)

//   return data
// }

export async function makeEnv(envId) {
  log(`Making environment ${envId}`)

  const resp = await fetch(endpoints.make(envId), postOptions)
  const data = await resp.json()

  if (resp.status === 200) {
    log('Environment made:', data)
    return data
  }
  log('Error making environment:', data.error)
  throw Error(data.error)
}

export async function closeEnv(instanceId) {
  log(`Closing environment ${instanceId}`)

  const resp = await fetch(endpoints.close(instanceId), postOptions)
  const data = await resp.json()

  if (resp.status === 200) {
    log('Environment closed:', data)
    return data
  }
  log('Error closing environment:', data.error)
  throw Error(data.error)
}

export async function startEnv(instanceId, assignmentId, qsParams = {}) {
  log(`Starting environment ${instanceId}`)

  const qs = obj2qs(qsParams)

  const url = endpoints.start(instanceId) + (qs ? `?${qs}` : '')
  const body = assignmentId
  const resp = await fetch(url, { ...postOptions, body })
  const data = await resp.json()

  if (resp.status === 200) {
    log('Environment started:', data)
    return data
  }
  log('Error starting environment:', data.error)
  throw Error(data.error)
}

// export async function listEnvs(withGames) {
//   log('Listing instantiated envs. With games:', Boolean(withGames))

//   const qs = withGames ? '?with_games=true' : ''
//   const resp = await fetch(endpoints.listEnvs + qs, reqOptions)
//   const data = await resp.json()

//   log('Instances loaded:', data)

//   return data
// }

// export async function listEnvsWithGames(worker_id = '') {
//   log('Listing only envs with games...')

//   const resp = await fetch(endpoints.listEnvsWithGames(worker_id), reqOptions)
//   const data = await resp.json()

//   log('Instances loaded:', data)

//   return data
// }

// export async function listHitsWithTurks(token = '') {
//   log('Listing only envs with games...')

//   const resp = await fetch(endpoints.listHitsWithTurks(token), reqOptions)
//   const data = await resp.json()

//   log('Instances loaded:', data)

//   return data
// }

// export async function listSteps(gameId) {
//   log(`Listing steps for game ${gameId}...`)

//   const resp = await fetch(endpoints.listSteps(gameId), reqOptions)
//   const data = await resp.json()

//   log('Steps loaded:', data)

//   return data
// }

// export async function stepImage(gameId, stepIter, agentKey) {
//   log(`Fetching base64 image data for agent ${agentKey}, step ${stepIter} in game ${gameId}...`)

//   const resp = await fetch(endpoints.stepImage(gameId, stepIter, agentKey))
//   const imageData = await resp.text()

//   // log('Base64 image data:', imageData)

//   return imageData
// }

export async function sessionSetup(sessionSetupInput) {
  log('Session Input:', sessionSetupInput)

  const body = JSON.stringify(sessionSetupInput)
  const resp = await fetch(endpoints.sessionSetup, { ...postOptions, body })
  const data = await resp.json()

  if (resp.status === 200) {
    log('Session details:', data)
    return data
  }

  log('Error initialiying session:', data.error)
  throw Error(data.error)
}

export async function sessionToken(visit_id) {
  log(`Fetching secret token for visit_id ${visit_id}...`)

  const resp = await fetch(endpoints.sessionToken(visit_id))
  const data = await resp.json()

  if (resp.status === 200) {
    const { token } = data
    log('Secret token:', token)
    return token
  }

  log('Error fetching token:', data.error)
  throw Error(data.error)
}

export async function collectUserData(inputValue) {
  log('collectUserData input:', inputValue)

  const body = JSON.stringify(inputValue)
  const resp = await fetch(endpoints.collectUserData, { ...postOptions, body })
  const data = await resp.json()

  if (resp.status === 200) {
    log('collectUserData response:', data)
    return data
  }

  log('Error when posting to collectUserData endpoint:', data.error)
  throw Error(data.error)
}

export async function getScores(visit_id) {
  log('Getting scores for this visit...')

  const resp = await fetch(endpoints.get_scores(visit_id))
  const data = await resp.json()

  if (resp.status === 200) {
    return {
      data,
    }
  }
  if (resp.status === 404) {
    // eslint-disable-next-line no-alert
    window.alert(data.error)
  }
  log('Error getting scores:', data.error)
  throw Error(data.error)
}

export async function getTaskChoices(inputValue) {
  log('Getting task choices for this visit...')

  const body = JSON.stringify(inputValue)
  const resp = await fetch(endpoints.get_task_choices, { ...postOptions, body })
  const data = await resp.json()

  log('DATA')
  log(data)
  if (resp.status === 200) {
    return {
      data,
    }
  }
  // if (resp.status === 404) {
  //   window.alert(data.error)
  // }
  log('Error getting task choices:', data.error)
  throw Error(data.error)
}

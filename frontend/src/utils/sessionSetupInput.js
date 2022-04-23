import { v4 as uuidv4 } from 'uuid'
import {
  defaultEnvId, noHitId, noTaskId,
} from '../config'

export default function getSessionSetupInput() {
  const { location } = window
  const urlParams = new URLSearchParams(location.search)

  const userType = urlParams.get('f') || urlParams.get('from') || localStorage.userType || 'local'
  const assignmentId = urlParams.get('assignmentId') || localStorage.assignmentId || uuidv4()
  // TODO remove environmentId - not really used anymore?
  const environmentId = urlParams.get('environmentId') || localStorage.environmentId || defaultEnvId
  const hitId = urlParams.get('hitId') || localStorage.hitId || noHitId
  const taskId = urlParams.get('t') || urlParams.get('taskId') || localStorage.taskId || noTaskId
  const workerId = urlParams.get('workerId') || localStorage.workerId || uuidv4()
  const original_url = location.href
  const { referrer } = document.referrer

  const sessionSetupInput = {
    assignmentId,
    workerId,
    hitId,
    environmentId,
    taskId,
    userType,
    original_url,
    referrer,
  }

  localStorage.assignmentId = assignmentId
  localStorage.environmentId = environmentId
  localStorage.hitId = hitId
  localStorage.taskId = taskId
  localStorage.workerId = workerId
  localStorage.userType = userType

  return sessionSetupInput
}

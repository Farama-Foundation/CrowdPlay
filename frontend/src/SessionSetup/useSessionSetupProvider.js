import {
  useState,
  useEffect,
  useCallback,
} from 'react'
import debug from 'debug'
import { api, useAsyncAction } from '../utils'

import getSessionSetupInput from '../utils/sessionSetupInput'

const log = debug('atari:useSessionSetupProvider')

export default function useSessionSetupProvider(task) {
  const [sessionSetupDetails, setSessionSetup] = useState(null)
  const querySessionSetupCallback = useCallback(sessionInput => api.sessionSetup(sessionInput), [])
  const [loadingSessionSetup, querySessionSetup] = useAsyncAction(querySessionSetupCallback)

  useEffect(() => {
    const { location, history } = window
    sessionStorage.original_url = location.href

    const sessionSetupInput = getSessionSetupInput()
    sessionSetupInput.taskId = task

    // Let's remove the query string from the browser url, if we're coming from mTurk
    if (sessionSetupInput.userType === 'mturk') {
      const [sanitizedUrl] = location.href.split('?')
      history.replaceState({}, '', sanitizedUrl)
    }

    (async () => {
      const sessionDetails = await querySessionSetup(sessionSetupInput)
      log('Session details:', sessionDetails)
      // Redirect immediately if told by API.
      if ('redirect' in sessionDetails) {
        window.location = sessionDetails.redirect
      } else {
        setSessionSetup(sessionDetails)
        localStorage.visit_id = sessionDetails.visit_id
      }
      // TODO: handle error from backend
    })()
  }, [querySessionSetup, task])

  return {
    sessionSetupDetails,
    loadingSessionSetup,
  }
}

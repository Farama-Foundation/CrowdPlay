/* eslint-disable no-alert */
import {
  useCallback,
  useContext,
  useState,
  useEffect,
} from 'react'
import debug from 'debug'
import SessionSetupContext from './SessionSetupContext'
import { api, emitter } from '../utils'

const log = debug('atari:useStartModal')

export default function useStartModal() {
  const [visible, setVisible] = useState(false)
  const [inputValue, setInputValue] = useState('Enter email address here...')
  const { sessionSetupDetails, loadingSessionSetup } = useContext(SessionSetupContext)

  const handleOk = useCallback(async () => {
    // Send to API endpoint if we're collecting email address
    if (sessionSetupDetails && sessionSetupDetails.user_type === 'email') {
      if (/@/.test(inputValue)
       // eslint-disable-next-line max-len
       || window.confirm('We are not sure if that is a valid email address. Please click Cancel to change it. Or click OK to proceed, but please note that you need to provide a valid email address to enter the raffle.')) {
        log('Input value:', inputValue)
        const input = {
          visit_id: sessionSetupDetails.visit_id,
          key: 'email',
          value: inputValue,
        }
        await api.collectUserData(input)
        setVisible(false) // this will hide the modal
      }
    } else {
      setVisible(false) // this will hide the modal
    }
    // TODO Why is sessionSetupDetails Null if people haven't edited the text field?!
    if (inputValue === 'Enter email address here...' && localStorage.userType === 'email') {
      // eslint-disable-next-line max-len
      if (!window.confirm('We are not sure if that is a valid email address. Please click Cancel to change it. Or click OK to proceed, but please note that you need to provide a valid email address to enter the raffle.')) {
        setVisible(true)
      }
    }
    emitter.emit('show_consent_modal')
  }, [inputValue, sessionSetupDetails])

  useEffect(() => (
    setVisible(!loadingSessionSetup && Boolean(sessionSetupDetails))
  ), [loadingSessionSetup, sessionSetupDetails])

  const inputChange = useCallback(value => setInputValue(value), [])

  return {
    sessionSetupDetails,
    visible,
    inputValue,
    handleOk,
    inputChange,
  }
}

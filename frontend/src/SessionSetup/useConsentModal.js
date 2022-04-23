import {
  useCallback,
  useContext,
  useState,
} from 'react'
import SessionSetupContext from './SessionSetupContext'
import { emitter } from '../utils'

export default function useConsentModal() {
  const [visible, setVisible] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const { sessionSetupDetails } = useContext(SessionSetupContext)

  const handleOk = useCallback(async () => {
    setVisible(false) // this will hide the modal
    localStorage.setItem('consent_obtained', true)
  }, [])

  const showConsentModal = () => {
    if (localStorage.getItem('consent_obtained') !== 'true') {
      setVisible(true)
    }
  }

  emitter.on('show_consent_modal', showConsentModal)

  const inputChange = useCallback(value => setInputValue(value), [])

  return {
    sessionSetupDetails,
    visible,
    inputValue,
    handleOk,
    inputChange,
  }
}

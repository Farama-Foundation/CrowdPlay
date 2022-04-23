import {
  useCallback,
  useState,
} from 'react'
import debug from 'debug'
import { api, emitter } from '../utils'

const log = debug('atari:useFeedbackModal')

export default function useFeedbackModal() {
  const [visible, setVisible] = useState(false)
  const [inputValue, setInputValue] = useState(null)

  const showFeedbackModalCallback = () => {
    setVisible(true)
  }

  emitter.on('show_feedback_modal', showFeedbackModalCallback)

  const handleOk = useCallback(async () => {
    //   Hide the modal first.
    setVisible(false) // this will hide the modal
    log('Input value:', inputValue)
    const input = {
      visit_id: localStorage.visit_id,
      key: 'feedback',
      value: inputValue,
    }
    await api.collectUserData(input)
  }, [inputValue])

  const handleCancel = () => {
    setVisible(false)
  }

  const inputChange = useCallback(value => setInputValue(value), [])

  return {
    visible,
    inputValue,
    handleOk,
    handleCancel,
    inputChange,
  }
}

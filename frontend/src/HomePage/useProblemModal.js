import {
  useCallback,
  useState,
  useEffect,
} from 'react'
import debug from 'debug'
import { api, emitter } from '../utils'

const log = debug('atari:useProblemModal')

export default function useProblemModal() {
  const [visible, setVisible] = useState(false)
  const [inputValue, setInputValue] = useState(null)

  useEffect(() => {
    const showProblemModalCallback = () => {
      setVisible(true)
    }
    emitter.on('show_problem_modal', showProblemModalCallback)
  }, [])
  const handleOk = useCallback(async () => {
    //   Hide the modal first.
    setVisible(false) // this will hide the modal
    log('Input value:', inputValue)
    const input = {
      visit_id: localStorage.visit_id,
      key: 'problem',
      value: inputValue,
    }
    await api.collectUserData(input)
    setInputValue('')
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

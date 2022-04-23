import {
  useCallback,
  useEffect,
  useState,
  useContext,
} from 'react'
import './Header.less'
import { Space, Modal, Button } from 'antd'
import { useHistory } from 'react-router-dom'
import { SessionSetupContext } from '../SessionSetup'
import JobDone from './JobDone'
import { emitter } from '../utils'

const getOrientation = () => window.screen.orientation.type

const useScreenOrientation = () => {
  const [orientation, setOrientation] = useState(getOrientation())

  const updateOrientation = () => {
    setOrientation(getOrientation())
  }

  useEffect(() => {
    window.addEventListener(
      'orientationchange',
      updateOrientation,
    )
    return () => {
      window.removeEventListener(
        'orientationchange',
        updateOrientation,
      )
    }
  }, [])

  return orientation
}

export default function GetTokenButton() {
  const { sessionSetupDetails } = useContext(SessionSetupContext)
  const { visit_id } = sessionSetupDetails ?? {}
  const [tokenButtonState, setTokenButtonState] = useState(true)
  const history = useHistory()
  const orientation = useScreenOrientation()

  const taskDoneCallback = () => {
    setTokenButtonState(false)
  }

  emitter.on('task_done_button', taskDoneCallback)

  const openTokenDialog = useCallback(() => {
    Modal.info({
      title: 'Job Done',
      content: <JobDone visit_id={visit_id} />,
    })
  }, [visit_id])

  const goToResults = () => {
    history.push(`/score/${sessionSetupDetails.visit_id}`)
  }

  const showProblemModal = () => {
    emitter.emit('show_problem_modal')
  }

  const problemtext = orientation === 'landscape-primary' ? 'Report Problem' : 'Problem'
  const finishtext = orientation === 'landscape-primary' ? 'Finish Experiment' : 'Finish'
  const tokentext = orientation === 'landscape-primary' ? 'Get Token' : 'Token'

  if (sessionSetupDetails) {
    return (
      <Space align="center" className="buttonspace">
        <Button
          type="primary"
          onClick={showProblemModal}
          className="button"
        >
          {problemtext}
        </Button>
        {(localStorage.userType === 'mturk')
            && (
              <Button
                disabled={tokenButtonState}
                type="primary"
                onClick={openTokenDialog}
                className="button"
              >
                {tokentext}
              </Button>
            )}

        {(localStorage.userType !== 'mturk')
            && (
            <Button
              disabled={tokenButtonState}
              type="primary"
              onClick={goToResults}
              className="button"
            >
              {finishtext}
            </Button>
            )}
      </Space>
    )
  }

  return null
}

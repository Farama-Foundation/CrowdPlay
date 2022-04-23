import React, { useEffect, useState } from 'react'
import PropTypes from 'prop-types'
import { Button } from 'antd'
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import { countDownStartBetweenGames } from '../config'
import { EnvState, emitter } from '../utils'
import './Environment.less'

export default function StartButton(props) {
  const {
    state,
    onButton,
    onStart,
  } = props

  const [countDown, setCountDown] = useState(-1)

  // Define countdown start
  useEffect(() => {
    const tvCountdownStart = (time) => {
      setCountDown(time)
    }

    emitter.on('tv-countdown-start', tvCountdownStart)
  }, [])

  useEffect(() => {
    // Starts countdown when we're ready to go
    if (countDown > 0) {
      setTimeout(() => setCountDown(countDown - 1), 1000) // keep counting down
    } else if (countDown === 0) {
      setCountDown(-1) // If countdown is done reset to -1
      onStart() // and start the episode
    }
  }, [countDown, onStart])

  useEffect(() => {
    // Resets the coundown when the game is over
    if (state === EnvState.EPISODE_ENDED) {
      setCountDown(countDownStartBetweenGames)
    }
  }, [state])

  let textToDisplay

  // TODO: multiline?
  switch (true) {
    case state === EnvState.READY:
      textToDisplay = <div>Waiting for the other players to join...</div>
      break
    case state === EnvState.COUNTDOWN:
      textToDisplay = (
        <div>
          {state === EnvState.EPISODE_ENDED ? <h2>Game Over</h2> : null}
          <span>Get ready! Next game starting in...</span>
          <br />
          <span className="countdown_number">{countDown}</span>
        </div>
      )
      break
    default:
      break
  }

  if (state !== EnvState.STARTED) {
    return (
      <div className="envstate_overlay">
        {/* <Modal
        visible={state !== EnvState.STARTED}
        closable={false}
        footer={null}
        maskClosable={false}
      > */}
        {textToDisplay && state !== EnvState.NOTREADY && (
        <div className="state_info">{textToDisplay}</div>
        )}

        {state === EnvState.NOTREADY && (
        <Button
          size="large"
          shape="round"
          onClick={onButton}
          loading={state === EnvState.STARTING}
          icon={state === EnvState.EPISODE_ENDED ? <ReloadOutlined /> : <PlayCircleOutlined />}
          type="primary"
        >
            {state === EnvState.EPISODE_ENDED ? 'Restart' : 'Start'}
        </Button>
        )}
        {/* </Modal> */}
      </div>

    )
  }
  return null
}

StartButton.propTypes = {
  state: PropTypes.number,
  onButton: PropTypes.func,
  onStart: PropTypes.func,
}

StartButton.defaultProps = {
  state: EnvState.NOTREADY,
  onButton: () => false,
  onStart: () => false,
}

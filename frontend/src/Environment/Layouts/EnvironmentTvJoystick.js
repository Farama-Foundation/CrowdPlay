import React, { useCallback } from 'react'
import PropTypes from 'prop-types'
import { Joystick, JoystickShape } from 'react-joystick-component'
import TV from './TV'

export default function EnvironmentTvJoystick(props) {
  const {
    env,
    envState,
    obsState,
    socketEnv,
  } = props

  const instanceId = env.instance_id
  const agentKey = env.agent_key

  const onMove = useCallback((stick) => {
    let ac
    ac = 0
    if (stick.x > 20 && stick.x > stick.y) {
      ac = 2
    }
    if (stick.x < -20 && -stick.x > stick.y) {
      ac = 3
    }
    if (stick.y > 20 && stick.y > Math.abs(stick.x)) {
      ac = 1
    }
    
    socketEnv.push_action(instanceId, agentKey, ac)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socketEnv, instanceId, agentKey])

  const onStop = useCallback(() => {
    socketEnv.push_action(instanceId, agentKey, 0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socketEnv, instanceId, agentKey])

  return (
    <div className="EnvironmentTVJoystick">
      <TV
        state={envState}
        obsState={obsState}
      />
      <div className="joystick_container">
        <Joystick
          throttle={100}
          baseShape={JoystickShape.Square}
          move={onMove}
          stop={onStop}
          minDistance={20}
        />
      </div>
    </div>
  )
}

EnvironmentTvJoystick.propTypes = {
  env: PropTypes.object,
  envState: PropTypes.number,
  obsState: PropTypes.object,
  socketEnv: PropTypes.object.isRequired,
}

EnvironmentTvJoystick.defaultProps = {
  env: null,
  envState: 0,
  obsState: {
    step_iter: -1, reward: '-', obs: {}, task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  },
}

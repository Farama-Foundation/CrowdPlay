import React, { useCallback } from 'react'
import PropTypes from 'prop-types'
import { Joystick, JoystickShape } from 'react-joystick-component'
import './EnvironmentPendulum.less'

export default function EnvironmentPendulum(props) {
  const {
    env,
    obsState,
    socketEnv,
  } = props

  const instanceId = env.instance_id
  const agentKey = env.agent_key

  const onMove = useCallback((stick) => {
    socketEnv.push_action(instanceId, agentKey, [0.02 * stick.x])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socketEnv, instanceId, agentKey])

  const onStop = useCallback(() => {
    socketEnv.push_action(instanceId, agentKey, [0])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socketEnv, instanceId, agentKey])

  if (obsState.obs && obsState.obs !== {}) {
    return (
      <div className="EnvironmentPendulum">
        <div className="pendulum_image_container">
          <img src={obsState.obs} alt="obs" className="pendulum_image" />
        </div>
        <div className="joystick_container">
          <span className="score">
            Score:
            {' '}
            {obsState.score}
          </span>
          <Joystick
            throttle={100}
            baseShape={JoystickShape.Square}
            move={onMove}
            stop={onStop}
          />
        </div>
      </div>
    )
  }

  return null
}

EnvironmentPendulum.propTypes = {
  env: PropTypes.object,
  obsState: PropTypes.object,
  socketEnv: PropTypes.object.isRequired,
}

EnvironmentPendulum.defaultProps = {
  env: null,
  obsState: {
    step_iter: -1, reward: '-', obs: {}, task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  },
}

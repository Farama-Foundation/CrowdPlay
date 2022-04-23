/* eslint-disable react/jsx-props-no-spreading */
import './Environment.less'
import PropTypes from 'prop-types'
import useEnvironment from './useEnvironment'
import StartButton from './StartButton'

import EnvironmentTv from './Layouts/EnvironmentTv'
import EnvironmentKeycatcher from './Layouts/EnvironmentKeycatcher'
import EnvironmentText from './Layouts/EnvironmentText'
import EnvironmentTvJoystick from './Layouts/EnvironmentTvJoystick'
import EnvironmentPendulum from './Layouts/EnvironmentPendulum'
import EnvironmentMinimalImage from './Layouts/EnvironmentMinimalImage'

const layouts = {
  taxi: EnvironmentText,
  atari: EnvironmentTv,
  atari_joystick: EnvironmentTvJoystick,
  pendulum: EnvironmentPendulum,
  keycatcher: EnvironmentKeycatcher,
  minimal_image: EnvironmentMinimalImage,
  default: EnvironmentTv,
}

export default function Environment(props) {
  const { instance } = props

  const params = useEnvironment(instance)

  // Render all the layout components returned from the backend.
  // Usually, this will be a single visible component.
  // But this way, we can easily combine that with different keycatchers.
  const componentsToRender = params.sessionSetupDetails.ui_layout.map(comp => layouts[comp])
  return (
    <>
      <StartButton onStart={params.start} state={params.envState} onButton={params.onButton} />
      {componentsToRender.map(Component => (<Component {...params} />))}
    </>
  )
}

Environment.propTypes = {
  instance: PropTypes.shape({
    instance_id: PropTypes.string,
    action_space: PropTypes.object,
    observation_space: PropTypes.object,
  }).isRequired,
}

Environment.defaultProps = {
}

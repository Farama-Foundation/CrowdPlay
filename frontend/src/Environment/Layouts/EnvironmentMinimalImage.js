import React from 'react'
import PropTypes from 'prop-types'

export default function EnvironmentMinimalImage({ obsState }) {
  if (obsState.step_iter >= 0) {
    return (
      <img src={obsState.obs} width="640px" height="320px" alt="obs" />
    )
  }
  return null
}

EnvironmentMinimalImage.propTypes = {
  obsState: PropTypes.object,
}

EnvironmentMinimalImage.defaultProps = {
  obsState: {
    step_iter: -1,
  },
}

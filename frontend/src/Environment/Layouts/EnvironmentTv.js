import React from 'react'
import PropTypes from 'prop-types'
import TV from './TV'

export default function EnvironmentTv(props) {
  const {
    extraRef,
    envState,
    sessionSetupDetails,
    obsState,
  } = props

  const task_has_requirements = obsState?.task_info.filter(info => 'required' in info).length > 0 || false

  const lis_task_info_required = obsState?.task_info
    .filter(info => 'required' in info)
    .map(info => (
      <li>
        {info.name}
        :
        {info.state}
        {' '}
        
        {`(${info.required} required)` ?? ''}
      </li>
    )) || ''

  const lis_task_info_notrequired = obsState?.task_info
    .filter(info => !('required' in info))
    .map(info => (
      <li>
        {info.name}
        :
        {info.state}
      </li>
    )) || ''

  return (
    <div className="Environment">
      <div className="grid">
        <div className="row">
          <TV
            state={envState}
            obsState={obsState}
            defaultScale={3}
          />

          <div className="observation-info">
            <div ref={extraRef}>
              <span style={{ alignContent: 'center' }}>
                <strong>
                  Score:
                  {obsState?.score || ' - '}
                </strong>
              </span>
              <hr />
              {obsState?.obs?.image && (
                Object.keys(obsState?.obs ?? {})
                  .filter(key => key !== 'Estimated Bonus Payment')
                  .filter(key => key !== 'image')
                  .length > 0 && (
                    <>
                      <span style={{ alignContent: 'center' }}><strong>Info:</strong></span>
                      <ul>
                        {Object
                          .keys(obsState.obs ?? {})
                          .filter(key => key !== 'Estimated Bonus Payment')
                          .filter(key => key !== 'image')
                          .map(key => `<li>${key}: ${obsState[key]}</li>`)
                          .join('')}
                      </ul>
                      <hr />
                    </>
                )
              )}

              {localStorage.userType === 'mturk' && (
              <>
                <strong>
                  Task progress: $
                  {obsState?.task_complete}
                </strong>
                <br />
                <strong>
                  Estimated bonus payment: $ $
                  {obsState?.task_bonus}
                </strong>
                <hr />
              </>
              )}

              {
                  task_has_requirements && (
                    
                  <>
                    <span>Progress:</span>
                    <ul>
                      {lis_task_info_required}
                    </ul>
                    <hr />
                    <span>Other fun statistics:</span>

                  </>
                  )
                }
              {
                  !task_has_requirements && (
                    <span>Other fun statistics:</span>
                  )
                }
              <ul>
                {lis_task_info_notrequired}
              </ul>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="instructions">
            {sessionSetupDetails && (
            <>
              <strong>Instructions:</strong>
              <div>{sessionSetupDetails.initial_message}</div>
            </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

EnvironmentTv.propTypes = {
  extraRef: PropTypes.object,
  envState: PropTypes.number,
  sessionSetupDetails: PropTypes.object,
  obsState: PropTypes.object,
}

EnvironmentTv.defaultProps = {
  extraRef: null,
  envState: 0,
  sessionSetupDetails: null,
  obsState: {
    step_iter: -1, reward: '-', obs: {}, task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  },
}

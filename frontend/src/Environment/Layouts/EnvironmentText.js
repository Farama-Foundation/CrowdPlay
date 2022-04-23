import React from 'react'
import PropTypes from 'prop-types'
import TVtext from './TV_text'

export default function EnvironmentText(props) {
  const {
    sessionSetupDetails,
    obsState,
  } = props

  const task_has_requirements = obsState?.task_info.filter(info => 'required' in info).length > 0 || false

  const lis_task_info_required = obsState?.task_info
    .filter(info => 'required' in info)
    .map(info => (
      <li key={info.name}>
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
      <li key={info.name}>
        {info.name}
        :
        {info.state}
      </li>
    )) || ''

  return (
    <div className="Environment">
      <div className="grid">
        <div className="row">
          <TVtext
            width={480}
            height={288}
            obsState={obsState}
          />

          <div className="observation-info">
            <div>
              <span style={{ alignContent: 'center' }}>
                <strong>
                  Score:
                  {obsState?.score || ' - '}
                </strong>
              </span>
              <hr />
              {obsState?.obs?.ascii && (
                Object.keys(obsState?.obs ?? {})
                  .filter(key => key !== 'Estimated Bonus Payment')
                  .filter(key => key !== 'image')
                  .filter(key => key !== 'ascii')
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

EnvironmentText.propTypes = {
  sessionSetupDetails: PropTypes.object,
  obsState: PropTypes.object,
}

EnvironmentText.defaultProps = {
  sessionSetupDetails: null,
  obsState: {
    step_iter: -1, reward: '-', task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  },
}

import './TV_text.less'
import PropTypes from 'prop-types'
import Ansi from 'ansi-to-react'

export default function TVtext(props) {
  const {
    width, height, obsState,
  } = props

  return (
    <div className="TVtext" style={{ width, height }}>
      <div className="frame">
        <div className="viewport">

          {/* <StartButton state={state} onButton={onButton} onStart={onStart} /> */}

          <div>
            <div>
              {obsState?.obs
                && (typeof obsState.obs === 'string' || obsState.obs instanceof String)
                && (obsState.obs.split('\n').map(i => <div><Ansi>{i}</Ansi></div>))}
            </div>

          </div>
        </div>
      </div>
      <div className="stand" />
    </div>
  )
}

TVtext.propTypes = {
  width: PropTypes.number,
  height: PropTypes.number,
  obsState: PropTypes.object,
}

TVtext.defaultProps = {
  width: 200,
  height: 200,
  obsState: {
    step_iter: -1, reward: '-', obs: {}, task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  },
}

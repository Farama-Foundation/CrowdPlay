import './TV.less'
import PropTypes from 'prop-types'
import { useState } from 'react'
import {
  Slider,
  Form,
} from 'antd'
import { EnvState } from '../../utils'

export default function TV(props) {
  const {
    state, defaultWidth, defaultHeight, obsState, defaultScale,
  } = props

  const [size, setSize] = useState(defaultScale)

  const width = defaultWidth * size
  const height = defaultHeight * size

  const sizeMarks = {
    1: '×1',
    1.5: '×1.5',
    2: '×2',
    2.5: '×2.5',
    3: '×3',
    3.5: '×3.5',
    4: '×4',
  }

  return (
    <div className="TVContainer">
      <div className="TV" style={{ width, height }}>
        <div className="frame">
          <div className="viewport">

            <img
              alt="Game screen"
              className={state === EnvState.STARTED ? 'display-block' : ''}
              src={obsState?.obs?.image || obsState?.obs}
            />

            <p />
          </div>
        </div>
        <div className="stand" />
      </div>
      <Form
        className="flex-space-between"
        size="large"
        layout="inline"
      >

        <Form.Item label="Screen Size">
          <Slider
            className="scaler"
            min={1}
            max={4}
            value={size}
            step={0.5}
            marks={sizeMarks}
            included={false}
            onChange={setSize}
            tipFormatter={value => `×${value}`}
          />
        </Form.Item>

      </Form>

    </div>
  )
}

TV.propTypes = {
  state: PropTypes.number,
  defaultWidth: PropTypes.number,
  defaultHeight: PropTypes.number,
  defaultScale: PropTypes.number,
  obsState: PropTypes.object,
}

TV.defaultProps = {
  state: EnvState.NOTREADY,
  defaultWidth: 320,
  defaultHeight: 192,
  defaultScale: 1,
  obsState: {
    step_iter: -1, reward: '-', obs: {}, task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  },
}

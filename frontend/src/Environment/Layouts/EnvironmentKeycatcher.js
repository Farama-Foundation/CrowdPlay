import React, {
  useEffect,
  useMemo,
} from 'react'
import PropTypes from 'prop-types'
import KeysCatcher from '../../models/KeysCatcher'

const keymaps = {
  default: {
    32: 0, // spacebar = advance one frame
  },
  taxi: {
    37: 3,
    38: 1,
    39: 2,
    40: 0,
    81: 4,
    65: 5,
  },
  taxi_waitforkey: {
    37: 3,
    38: 1,
    39: 2,
    40: 0,
    81: 4,
    65: 5,
    // Send -1 to backend to signal that all keys have been released
    '': -1,
  },
  multiagent_atari_leftrightfire: {
    32: { game: 1 }, // space = fire
    39: { game: 2 }, // right arrow = right
    37: { game: 3 }, // left arrow = left
    '32,39': { game: 4 }, // space + right arrow = right + fire
    '32,37': { game: 5 }, // space + left arrow = left + fire
    '': { game: 0 }, // no key pressed = noop
  },
  multiagent_atari_updownleftrightfire: {
    32: { game: 1 }, // Fire (space)
    38: { game: 2 }, // Up
    39: { game: 3 }, // Right
    37: { game: 4 }, // Left
    40: { game: 5 }, // Down
    '38,39': { game: 6 }, // UP RIGHT
    '37,38': { game: 7 }, // UP LEFT
    '39,40': { game: 8 }, // DOWN RIGHT
    '37,40': { game: 9 }, // DOWN LEFT
    '32,38': { game: 10 }, // FIRE Up
    '32,39': { game: 11 }, // FIRE Right
    '32,37': { game: 12 }, // FIRE Left
    '32,40': { game: 13 }, // FIRE Down
    '32,38,39': { game: 14 }, // FIRE UP RIGHT
    '32,37,38': { game: 15 }, // FIRE UP LEFT
    '32,39,40': { game: 16 }, // FIRE DOWN RIGHT
    '32,37,40': { game: 17 }, // FIRE DOWN LEFT
    '': { game: 0 }, // no key pressed = noop
  },
  multiagent_atari_updownleftright: {
    38: { game: 1 }, // Up
    39: { game: 2 }, // Right
    37: { game: 3 }, // Left
    40: { game: 4 }, // Down
    '38,39': { game: 5 }, // UP RIGHT
    '37,38': { game: 6 }, // UP LEFT
    '39,40': { game: 7 }, // DOWN RIGHT
    '37,40': { game: 8 }, // DOWN LEFT
  },
  atari_leftrightfire: {
    32: 1, // space = fire
    39: 2, // right arrow = right
    37: 3, // left arrow = left
    '32,39': 4, // space + right arrow = right + fire
    '32,37': 5, // space + left arrow = left + fire
    '': 0, // no key pressed = noop
  },
  atari_updownleftrightfire: {
    32: 1, // Fire (space)
    38: 2, // Up
    39: 3, // Right
    37: 4, // Left
    40: 5, // Down
    '38,39': 6, // UP RIGHT
    '37,38': 7, // UP LEFT
    '39,40': 8, // DOWN RIGHT
    '37,40': 9, // DOWN LEFT
    '32,38': 10, // FIRE Up
    '32,39': 11, // FIRE Right
    '32,37': 12, // FIRE Left
    '32,40': 13, // FIRE Down
    '32,38,39': 14, // FIRE UP RIGHT
    '32,37,38': 15, // FIRE UP LEFT
    '32,39,40': 16, // FIRE DOWN RIGHT
    '32,37,40': 17, // FIRE DOWN LEFT
    '': 0, // no key pressed = noop
  },
  atari_updownleftright: {
    38: 1, // Up
    39: 2, // Right
    37: 3, // Left
    40: 4, // Down
    '38,39': 5, // UP RIGHT
    '37,38': 6, // UP LEFT
    '39,40': 7, // DOWN RIGHT
    '37,40': 8, // DOWN LEFT
  },
}

const relevant_keys = {
  default: [32],
  taxi: [37, 38, 39, 40, 81, 65],
  taxi_waitforkey: [37, 38, 39, 40, 81, 65],
  atari_leftrightfire: [32, 39, 37],
  atari_updownleftrightfire: [32, 37, 38, 39, 40],
  atari_updownleftright: [38, 39, 37, 40],
  multiagent_atari_leftrightfire: [32, 39, 37],
  multiagent_atari_updownleftrightfire: [32, 37, 38, 39, 40],
  multiagent_atari_updownleftright: [38, 39, 37, 40],
}

export default function EnvironmentKeycatcher(props) {
  const {
    env,
    socketEnv,
    sessionSetupDetails,
  } = props

  const keysCatcher = useMemo(() => new KeysCatcher(), [])

  useEffect(() => {
    const instanceId = env.instance_id
    const agentKey = env.agent_key
    keysCatcher.installHandlers()
    
    const onKeychange = keycodes => {
      const keymap_id = sessionSetupDetails.ui_layout_options.keymap || 'default'
      // We first filter out only the relevant keys
      const relevant_keycodes = keycodes.filter(keycode => relevant_keys[keymap_id].includes(keycode))
      // Because then, we can just define an array for every combination of keys.
      // Now we check if the key combination is valid, if not we ignore it.
      // Depending on priorities, you could instead try to map this to the largest matching subset, for instance.
      if (relevant_keycodes in keymaps[keymap_id]) {
        const action = keymaps[keymap_id][relevant_keycodes]
        // socketEnv.push('action', instanceId, agentKey, stepIter, action)
        socketEnv.push_action(instanceId, agentKey, action)
      }
    }

    keysCatcher.on('keychange', onKeychange)

    return () => {
      keysCatcher.destroy()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (<> </>)
}

EnvironmentKeycatcher.propTypes = {
  env: PropTypes.object,
  socketEnv: PropTypes.object,
  sessionSetupDetails: PropTypes.object,
}

EnvironmentKeycatcher.defaultProps = {
  env: null,
  socketEnv: null,
  sessionSetupDetails: { ui_layout_options: { keymap: 'default' } },
}

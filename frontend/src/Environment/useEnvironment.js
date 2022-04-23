import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useContext,
} from 'react'
import debug from 'debug'
import SocketEnv from '../models/SocketEnv'
import { EnvState, emitter } from '../utils'
import { wsUri } from '../config'
import doorBellSound from '../assets/sounds/door-bell.wav'
import SessionSetupContext from '../SessionSetup/SessionSetupContext'

const log = debug('atari:useEnvironment')

export default function useEnvironment(env) {
  const { sessionSetupDetails } = useContext(SessionSetupContext)
  const [envState, setEnvState] = useState(EnvState.NOTREADY)
  const [obsState, setObsState] = useState({
    step_iter: -1, reward: '-', obs: {}, task_info: [], task_complete: '-', score: '-', task_bonus: '-',
  })
  const imgRef = useRef(null)
  const txtRef = useRef(null)
  const extraRef = useRef(null)

  // Some renaming
  const instanceId = env.instance_id
  const agentKey = env.agent_key

  // const keysCatcher = useMemo(() => new KeysCatcher(), [])
  const socketEnv = useMemo(() => new SocketEnv(), [])

  const start = () => {
    socketEnv.push('start', instanceId)
  }
  
  const onButton = () => {
    socketEnv.push('user_ready', instanceId, agentKey)
    setEnvState(EnvState.READY)
  }

  useEffect(() => {
    socketEnv.connect(wsUri)

    const onConnected = () => {
      socketEnv.push('setup_user', instanceId, agentKey)
    }

    const onForceDisconnected = (reason) => {
      log(`Disconnected. Reason: ${reason}. `)
      // keysCatcher.uninstallHandlers()
      setEnvState(EnvState.FAULT)
      emitter.emit('task_done_button')
      // eslint-disable-next-line no-alert
      window.alert(reason)
    }

    const onStarting = () => {
      setEnvState(EnvState.STARTING)
    }

    const onStarted = () => {
      // keysCatcher.installHandlers()
      setEnvState(EnvState.STARTED)
    }

    const onStep = step => {
      // Unpack all the values
      const {
        step_iter,
        task_complete,
      } = step

      setObsState(step)
      socketEnv.set_step_iter(step_iter)

      if (task_complete >= 1) {
        emitter.emit('task_done_button')
      }
    }

    const onEnd = () => {
      if (envState !== EnvState.FAULT) {
        setEnvState(EnvState.COUNTDOWN)
        setObsState({
          step_iter: -1,
          reward: obsState.reward,
          obs: {},
          task_info: obsState.task_info,
          task_complete: obsState.task_complete,
          score: obsState.score,
          task_bonus: obsState.task_bonus,
        })
        emitter.emit('tv-countdown-start', 3)
      }
    }

    const onCountdownStart = (time, playSound) => {
      if (playSound) {
        const doorBellAudio = new Audio(doorBellSound)
        doorBellAudio.play()
      }
      if (time > 0) {
        emitter.emit('tv-countdown-start', time)
        setEnvState(EnvState.COUNTDOWN)
      } else {
        setEnvState(EnvState.COUNTDOWN_DONE)
        start()
      }
    }

    socketEnv.on('connected', onConnected)
    socketEnv.on('starting', onStarting)
    socketEnv.on('started', onStarted)
    socketEnv.on('step', onStep)
    socketEnv.on('done', onEnd)
    socketEnv.on('force-disconnected', onForceDisconnected)
    socketEnv.on('countdown-start', onCountdownStart)

    return () => {
      socketEnv.destroy()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socketEnv, instanceId, agentKey])

  return {
    env,
    start,
    onButton,
    imgRef,
    extraRef,
    txtRef,
    envState,
    sessionSetupDetails,
    obsState,
    socketEnv,
  }
}

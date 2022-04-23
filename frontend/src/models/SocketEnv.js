import EventEmitter from 'events'
import { io } from 'socket.io-client'
import debug from 'debug'
import { Deferred } from '../utils'

const log = debug('atari:SocketEnv')

export default class SocketEnv extends EventEmitter {
  connection = null

  socket = null

  step_iter = 0

  set_step_iter = (step_iter) => {
    this.step_iter = step_iter
  }

  get isConnected() {
    return this.socket && this.socket.connected
  }

  waitConnection() {
    return this.connection.promise
  }

  onConnect = () => {
    log('Connection established.')
    this.connection.resolve()
    this.emit('connected')
  }

  onDisconnect = reason => {
    log('Disconnected:', reason)
    this.connection = null
    this.emit('disconnected')
  }

  onConnectError = error => {
    log('Connection error:', error)
    this.connection.reject()
    this.emit('connection-error')
  }

  onStep = stepInfo => {
    // log('Env Step:', stepInfo)
    this.emit('step', stepInfo)
  }

  // onStopped = () => {
  //   log('Env Stopped')
  //   this.emit('stopped')
  // }

  onDone = () => {
    log('Env Done')
    this.emit('done')
  }

  onError = error => {
    log('Env error:', error)
    this.emit('error', error)
  }

  // onChangePlayers = ({ num_agents_in_game, is_ready, play_sound }) => {
  //   log('Players changed to:', num_agents_in_game)
  //   this.emit('change-players', num_agents_in_game, is_ready, play_sound)
  // }

  onCountdownStart = ({ time, play_sound }) => {
    log('Game starting in ', time)
    this.emit('countdown-start', time, play_sound)
  }

  onForceDisconnected = ({ reason }) => {
    log('Force-Disconnected. Reason:', reason)
    this.emit('force-disconnected', reason)
  }

  onCanStart = () => {
    log('Env can start')
    this.emit('can-start')
  }

  onStarting = gameId => {
    log('Env starting. Game ID:', gameId)
    this.emit('starting', gameId)
  }

  onStarted = gameId => {
    log('Env started')
    this.emit('started', gameId)
  }

  connect(wsUri) {
    this.connection = new Deferred()
    this.socket = io(wsUri)
    this.installHandlers()

    return this.waitConnection()
  }

  installHandlers() {
    this.socket.on('connect', this.onConnect)
    this.socket.on('disconnect', this.onDisconnect)
    this.socket.on('connect_error', this.onConnectError)
    this.socket.on('step', this.onStep)
    // this.socket.on('stopped', this.onStopped)
    this.socket.on('done', this.onDone)
    this.socket.on('error', this.onError)
    // this.socket.on('change_agents', this.onChangePlayers)
    this.socket.on('can_start', this.onCanStart)
    this.socket.on('starting', this.onStarting)
    this.socket.on('started', this.onStarted)
    this.socket.on('force_disconnected', this.onForceDisconnected)
    this.socket.on('countdown_start', this.onCountdownStart)
  }

  uninstallHandlers(disconnect = true) {
    this.socket.offAny()
    if (disconnect) this.socket.disconnect()
  }

  push(event, ...args) {
    this.socket.emit(event, ...args)
  }

  push_action(instanceId, agentKey, action) {
    this.socket.emit('action', instanceId, agentKey, this.step_iter, action)
  }

  destroy() {
    this.uninstallHandlers()
    this.removeAllListeners()
  }
}

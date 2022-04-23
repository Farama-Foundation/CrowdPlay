import EventEmitter from 'events'
import debug from 'debug'

const log = debug('atari:KeysCatcher')

export default class KeysCatcher extends EventEmitter {
  keycodes = []

  keydownHandler = event => {
    const { keyCode } = event

    log(`keydown: ${keyCode}`)

    this.keycodes[keyCode] = keyCode
    this.emit('keychange', this.toList())
  }

  keyupHandler = event => {
    const { keyCode } = event

    log(`keyup: ${keyCode}`)

    this.keycodes[keyCode] = false
    this.emit('keychange', this.toList())
  }

  toList() {
    return this.keycodes.filter(keycode => Boolean(keycode))
  }

  installHandlers(empty = true) {
    log('Installing event handlers `keydown` and `keyup`')
    
    if (empty) this.keycodes.length = 0

    document.addEventListener('keydown', this.keydownHandler)
    document.addEventListener('keyup', this.keyupHandler)
  }

  uninstallHandlers(empty = true) {
    log('Uninstalling event handlers `keydown` and `keyup`')

    document.removeEventListener('keydown', this.keydownHandler)
    document.removeEventListener('keyup', this.keyupHandler)

    if (empty) this.keycodes.length = 0
  }

  destroy() {
    this.uninstallHandlers()
    this.removeAllListeners()
  }
}

export default class Deferred {
  resolve = null

  reject = null

  constructor() {
    this.promise = new Promise((resolve, reject) => {
      this.resolve = resolve
      this.reject = reject
    })
  }
}

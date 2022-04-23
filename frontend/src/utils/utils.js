export const noop = () => { }

export const obj2qs = obj => Object
  .entries(obj)
  .map(([key, value]) => `${key}=${value}`)
  .join('&')

export function secs2minsAndSecs(seconds) {
  // Hours, minutes and seconds
  const hrs = ~~(seconds / 3600)
  const mins = ~~((seconds % 3600) / 60)
  const secs = ~~seconds % 60

  // Output like "1:01" or "4:03:59" or "123:03:59"
  let ret = ''
  if (hrs > 0) {
    ret += `${hrs}:${(mins < 10 ? '0' : '')}`
  }

  ret += `${mins}:${(secs < 10 ? '0' : '')}`
  ret += secs

  return ret
}

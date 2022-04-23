import { useCallback, useState } from 'react'

export default function useAsyncAction(action) {
  const [loading, setLoading] = useState(false)

  const doAction = useCallback((...args) => {
    setLoading(true)
    return action(...args).finally(() => setLoading(false))
  }, [action, setLoading])

  return [loading, doAction]
}

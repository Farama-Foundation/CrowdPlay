import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAsyncAction, api } from '../utils'
import useColumnsConfig from './useColumnsConfig'

export default function useScorePage() {
  const { visitId } = useParams()
  const [scores, setScores] = useState([])
  const fetchScoresCallback = useCallback(_visitId => api.getScores(_visitId), [])
  const [loading, fetchScores] = useAsyncAction(fetchScoresCallback)

  const columnsConfig = useColumnsConfig()

  useEffect(() => {
    (async () => {
      const _scores = await fetchScores(visitId)
      setScores(_scores.data)
    })()
  }, [fetchScores, visitId])

  return {
    visitId,
    scores,
    loading,
    columnsConfig,
  }
}

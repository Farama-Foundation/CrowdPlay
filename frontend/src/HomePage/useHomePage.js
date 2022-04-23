import {
  useContext,
} from 'react'
import { SessionSetupContext } from '../SessionSetup'

export default function HomePage() {
  const { sessionSetupDetails, loadingSessionSetup } = useContext(SessionSetupContext)
  const { env } = sessionSetupDetails ?? {}

  return {
    env,
    loadingSessionSetup,
  }
}

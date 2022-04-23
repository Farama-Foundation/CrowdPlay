import PropTypes from 'prop-types'
import { useMemo } from 'react'
import SessionSetupContext from './SessionSetupContext'
import useSessionSetupProvider from './useSessionSetupProvider'
import ConsentModal from './ConsentModal'
import StartModal from './StartModal'

export default function SessionSetupProvider(props) {
  const { children, taskId } = props
  const {
    sessionSetupDetails,
    loadingSessionSetup,
  } = useSessionSetupProvider(taskId)

  const value = useMemo(() => ({ loadingSessionSetup, sessionSetupDetails }), [
    sessionSetupDetails,
    loadingSessionSetup,
  ])

  return (
    <SessionSetupContext.Provider value={value}>
      {children}
      <ConsentModal />
      <StartModal />
    </SessionSetupContext.Provider>
  )
}

SessionSetupProvider.propTypes = {
  children: PropTypes.node.isRequired,
  taskId: PropTypes.string,
}

SessionSetupProvider.defaultProps = {
  taskId: 'default',
}

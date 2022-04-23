import './HomePage.less'
import {
  Layout,
  Spin,
} from 'antd'
import useHomePage from './useHomePage'
import Environment from '../Environment'
import ProblemModal from './ProblemModal'

export default function HomePage() {
  const {
    env,
    loadingSessionSetup,
  } = useHomePage()

  return (
    <Layout.Content className="HomePage">

      <ProblemModal />

      {loadingSessionSetup && (
        <Spin
          className="loading-env"
          tip="Loading environment..."
          size="large"
        />
      )}

      {env && (
        <Environment
          instance={env}
        />
      )}
    </Layout.Content>
  )
}

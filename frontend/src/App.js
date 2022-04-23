import './App.less'
import {
  BrowserRouter as Router,
  Switch,
  Route,
} from 'react-router-dom'
import { Layout } from 'antd'
import { useState } from 'react'
import { SessionSetupProvider } from './SessionSetup'
import Header from './Header'
import HomePage from './HomePage'
// import GamesPage from './GamesPage'
// import HitsPage from './HitsPage'
// import StepsPage from './StepsPage'
import ScorePage from './ScorePage'
import EnvironmentChoicePage from './EnvironmentChoicePage/EnvironmentChoicePage'
import { emitter } from './utils'

export default function App() {
  const [taskChoice, setTaskChoice] = useState(false)

  const setTaskChoiceFn = (taskChoiceToSet) => {
    setTaskChoice(taskChoiceToSet)
  }

  emitter.on('task_choice_set', setTaskChoiceFn)

  return (
    <Layout className="App">
      <Router>
        <Switch>
          {/* <Route path="/games/:gameId/steps">
            <StepsPage />
          </Route>

          <Route path="/games/:gameId/video">
            <div>TODO: Video</div>
          </Route>

          <Route exact path="/games">
            <GamesPage />
          </Route>

          <Route exact path="/hits">
            <HitsPage />
          </Route> */}

          <Route path="/score/:visitId">
            <Header />
            <ScorePage />
          </Route>

          <Route exact path="/">
            {!taskChoice && (
            <>
              <Header />
              <EnvironmentChoicePage />
            </>
            )}
            {taskChoice && (
            <SessionSetupProvider taskId={taskChoice}>
              <Header include_buttons />
              <HomePage />
            </SessionSetupProvider>
            )}
          </Route>

          <Route path="*">
            <div>TODO: No match</div>
          </Route>
        </Switch>
      </Router>
    </Layout>
  )
}

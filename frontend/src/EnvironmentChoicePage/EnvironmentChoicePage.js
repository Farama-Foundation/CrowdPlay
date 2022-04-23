/* eslint-disable global-require */
/* eslint-disable import/no-dynamic-require */
import './EnvironmentChoicePage.less'
import { Button, Card, Space } from 'antd'
import {
  useEffect, useCallback, useState,
} from 'react'
import { emitter, api, useAsyncAction } from '../utils'
import getSessionSetupInput from '../utils/sessionSetupInput'

export default function EnvironmentChoicePage() {
  const { Meta } = Card
  const [taskChoices, setTaskChoices] = useState({ user_choice_available: true })
  
  const fetchTaskChoicesCallback = useCallback(_taskId => api.getTaskChoices(_taskId), [])
  const [loading, fetchTaskChoices] = useAsyncAction(fetchTaskChoicesCallback)

  const onChoice = (value) => {
    emitter.emit('task_choice_set', value)
  }

  useEffect(() => {
    (async () => {
      const _choices = await fetchTaskChoices(getSessionSetupInput())
      setTaskChoices(_choices.data)
    })()
  }, [fetchTaskChoices])

  if (!loading && taskChoices.user_choice_available === false) {
    // TODO this generates a warning. Fix this.
    emitter.emit('task_choice_set', taskChoices.choice)
    return null
  }

  const c = taskChoices.choices ?? []

  function choiceToCard(choice) {
    const image = require(`../assets/images/${choice.image}`).default
    return (
      <Card
        key={choice.value}
        hoverable
        style={{ width: 260 }}
        cover={choice.image && <img alt="gameplay" src={image} className="card-image" />}
      >
        <div className="card" id="test">
          <Meta title={choice.title} description={choice.description} />
          <div className="buttonDiv">
            <Button onClick={() => onChoice(choice.value)} className="envChoiceButton">
              <span>
                Launch
              </span>
            </Button>
          </div>
        </div>
      </Card>
    )
  }

  const components = c.map(taskChoice => choiceToCard(taskChoice))
  
  return (
    <Space align="center" size="large" wrap>
      {components}
    </Space>
    
  )
}

import './ScorePage.less'
import {
  Table,
  Typography,
  Button,
} from 'antd'
import useScorePage from './useScorePage'
import { emitter } from '../utils'
import FeedbackModal from './FeedbackModal'

const title = () => (
  <Typography.Title level={3}>
    How did you do?
  </Typography.Title>
)

export default function ScorePage() {
  const {
    scores,
    loading,
    columnsConfig,
  } = useScorePage()

  const newTask = () => {
    // history.push(sessionStorage.original_url);
    window.location.href = sessionStorage.original_url
  }

  const showFeedbackModal = () => {
    emitter.emit('show_feedback_modal')
  }

  const score = scores.filter(s => s.metric === 'Score (total)')[0]

  return (
    <>
      <FeedbackModal />
      
      <div className="ScorePage">
        {sessionStorage.original_url && (
          <div id="ScoreText">
            <p>
              Thank you for participating in our experiment. Below you can see how you comapared to other players.
              We tracked not only your score, but also other metrics like how long you played.
              For each of these, we show both your total over the entire experiment,
              but also the highest of any single game you played.
              For each metric we tracked, we show you both how you did yourself,
              but also how you compare to other players.
              {score && 'your_score' in score && (
                <span>
                  {' '}
                  For instance, you scored
                  {' '}
                  {score.your_score}
                  {' '}
                  points, which is higher than
                  {' '}
                  {score.percentile}
                  % of participants.
                  {' '}
                </span>
              )}
              To the right, you can also see how you did compared to everyone else in a visual way.
            </p>
            <p>
              We hope you enjoyed the experiment, and thank you for your participation!
              You can also start a new experiment if you would like to try some of the other games we have.
            </p>
            <Button
              type="primary"
              onClick={newTask}
              id="NewTaskButton"
            >
              <span>
                Start new game.
              </span>
            </Button>

            <Button
              type="primary"
              onClick={showFeedbackModal}
              id="feedbackModalButton"
            >
              <span>
                Leave Feedback.
              </span>
            </Button>
          </div>
        )}
        <Table
          title={title}
          rowKey="metric"
          loading={loading}
          dataSource={scores}
          // expandable={expandableConfig}
          columns={columnsConfig}
          pagination={false}
        />
      </div>
    </>
          
  )
}

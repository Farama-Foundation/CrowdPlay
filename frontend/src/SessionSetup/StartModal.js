import './Modal.less'
import { Button, Input, Modal } from 'antd'
import useStartModal from './useStartModal'

export default function StartModal() {
  const {
    sessionSetupDetails, // => /api/hello response
    visible,
    inputValue,
    handleOk,
    inputChange,
  } = useStartModal()

  return (
    <Modal
      visible={visible}
      // style={{ height: 'calc(100vh - 200px)' }}
      bodyStyle={{ overflowY: 'scroll' }}
      closable={false}
      maskClosable={false}
      onOk={handleOk}
      title="IMPORTANT INSTRUCTIONS"
      footer={(
        <Button
          type="primary"
          onClick={handleOk}
        >
          OK
        </Button>
      )}
    >
      {sessionSetupDetails && (<p>{sessionSetupDetails.initial_message}</p>)}

      <p>
        
        {sessionSetupDetails && sessionSetupDetails.user_type === 'mturk'
        && (
        <span>
          User your keyboard&apos;s arrow keys and space bar to interact with the game.
          It is up to you to follow the instructions above, please follow them carefully.
        </span>
        )}
        {sessionSetupDetails && sessionSetupDetails.user_type === 'email'
        && (
        <span>
          User your keyboard&apos;s arrow keys and space bar to interact with the game.
          It is up to you to follow the instructions above, please follow them carefully.
        </span>
        )}
        
      </p>

      {sessionSetupDetails
        && sessionSetupDetails.user_type === 'email'
        && (
        <p>
          If you would like to enter the raffle, please enter your email address below.
          During the game you will see a task completion counter next to the game screen.
          You must continue playing until the task completion counter shows at least 100% to be entered into the raffle.
        </p>
        )}

      {sessionSetupDetails
        && sessionSetupDetails.user_type === 'email'
        && (
        <p>
          {' '}
          <Input
            value={inputValue}
            onChange={({ target }) => inputChange(target.value)}
            placeholder="Enter something here..."
            style={{ width: '100%' }}
          />
        </p>
        )}

      <p>
        Please do not open multiple tabs or windows of this link at the same time. In a two-player task,
        if you are not being connected to another human player,
        or there appear to be issues (e.g. other player is not moving at all),
        please click ‘Reload’ in your browser window and tell the other player to do the same.
      </p>

      {
        window.navigator.userAgent.indexOf('Firefox') !== -1 && (
          <p>
            <strong style={{ color: 'red' }}>
              We have seen occasional reports of stuttering in Firefox.
              Please consider using this site in Chrome, Safari, or another browser,
              while we are working to fix this.
            </strong>
          </p>
        )
      }

      {
        (window.navigator.userAgent.indexOf('iPhone') !== -1
        || window.navigator.userAgent.indexOf('iPad') !== -1
        || window.navigator.userAgent.indexOf('Android') !== -1)
        && (
          <p>
            <strong style={{ color: 'red' }}>
              This website requires a keyboard to function.
              If your device does not have a keyboard, please consider visiting us from a desktop or laptop computer
              while we are working on touchscreen controls.
            </strong>
          </p>
        )
      }

    </Modal>
  )
}

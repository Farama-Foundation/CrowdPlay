import { Button, Input, Modal } from 'antd'
import useFeedbackModal from './useFeedbackModal'

const { TextArea } = Input

export default function FeedbackModal() {
  const {
    visible,
    inputValue,
    handleOk,
    handleCancel,
    inputChange,
  } = useFeedbackModal()

  return (
    <Modal
      visible={visible}
      // maskClosable={false}
      onOk={handleOk}
      onCancel={handleCancel}
      title="Feedback"
      footer={(
        <Button
          type="primary"
          onClick={handleOk}
        >
          Send
        </Button>
      )}
    >

      <p>
        If you would like to leave feedback, please do so below.
        This platform is anonymous, so we will not be able to contact you with a response.
        However, rest assured that we read all feedback carefully and use it to further
        improve our platform. We very much appreciate your time and efforts in writing to us.
      </p>

      <p>
        <TextArea
          value={inputValue}
          onChange={({ target }) => inputChange(target.value)}
          placeholder="Enter feedback here..."
          rows={4}
          style={{ width: '100%' }}
        />
      </p>

    </Modal>
  )
}

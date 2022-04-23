import { Button, Input, Modal } from 'antd'
import useProblemModal from './useProblemModal'

const { TextArea } = Input

export default function ProblemModal() {
  const {
    visible,
    inputValue,
    handleOk,
    handleCancel,
    inputChange,
  } = useProblemModal()

  return (
    <Modal
      visible={visible}
      // maskClosable={false}
      onOk={handleOk}
      onCancel={handleCancel}
      title="Problem"
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
        If you would like to let us know about a technical problem you encountered, please do so below.
        Please include as much details as possible, including what happened and what you were doing right
        before it happened.
        This platform is anonymous, so we will not be able to contact you with a response.
        However, rest assured that we read all feedback carefully and use it to further
        improve our platform. We very much appreciate your time and efforts in writing to us.
      </p>

      <p>
        We have had occasional reports of stuttering in Firefox. If you have encountered this, please consider using
        Chrome or Safari while we work to fix this issue. But please still let us know about it here.
      </p>

      <p>
        <TextArea
          value={inputValue}
          onChange={({ target }) => inputChange(target.value)}
          placeholder="Enter problem description here..."
          rows={4}
          style={{ width: '100%' }}
        />
      </p>

    </Modal>
  )
}

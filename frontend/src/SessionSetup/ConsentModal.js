import './Modal.less'
import { Button, Modal } from 'antd'
import useConsentModal from './useConsentModal'

export default function ConsentModal() {
  const {
    visible,
    handleOk,
  } = useConsentModal()
  // TODO make the modal scrollable.
  return (
    <Modal
      visible={visible}
      style={{ height: 'calc(100vh - 200px)' }}
      bodyStyle={{ overflowY: 'scroll' }}
      closable={false}
      maskClosable={false}
      onOk={handleOk}
      title="Consent Form"
      width="80%"
      footer={(
        <Button
          type="primary"
          onClick={handleOk}
        >
          OK
        </Button>
      )}
    >

      <h2>For Review Purposes Only</h2>

      <p>This is where the consent form would be, which has been removed to anonymize the submission.</p>

    </Modal>
  )
}

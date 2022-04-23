import { Input, Button, Alert } from 'antd'
import PropTypes from 'prop-types'
import {
  useEffect, useState, useCallback, useRef,
} from 'react'
import { CopyOutlined } from '@ant-design/icons'
import { api, useAsyncAction, If } from '../utils'

export default function JobDone(props) {
  const { visit_id } = props
  const [token, setToken] = useState('')
  const [forbidden, setForbidden] = useState(false)
  const inputRef = useRef(null)
  const fetchTokenCallback = useCallback(() => api.sessionToken(visit_id), [visit_id])
  const [fetchingToken, fetchToken] = useAsyncAction(fetchTokenCallback)

  const copyClick = useCallback(() => {
    const input = inputRef.current
    if (input) {
      input.select()
      document.execCommand('copy')
    }
  }, [])

  useEffect(() => {
    (async () => {
      try {
        const _token = await fetchToken()
        setToken(_token)
      } catch (err) {
        setForbidden(true)
      }
    })()
  }, [fetchToken])

  return (
    <div className="JobDone">
      <If
        condition={forbidden}
        thenBlock={(
          <Alert
            message="Forbidden"
            description="You haven't completed the task."
            type="error"
          />
        )}
        elseBlock={(
          <>
            <p>Please, follow the instructions:</p>
            <ol>
              <li>
                <div>Copy the token below</div>
                <Input.Group compact>
                  <Input
                    ref={inputRef}
                    disabled={fetchingToken}
                    style={{ width: '88%' }}
                    placeholder="Fetching token..."
                    value={token}
                  />
                  <Button
                    title="Copy token"
                    style={{ width: '12%' }}
                    icon={<CopyOutlined />}
                    onClick={copyClick}
                  />
                </Input.Group>
              </li>
              <li>Go back to MTurk console</li>
              <li>Paste this token inside the provided input</li>
              <li>Submit the assignment</li>
            </ol>
          </>
        )}
      />
    </div>
  )
}

JobDone.propTypes = {
  visit_id: PropTypes.number.isRequired,
}

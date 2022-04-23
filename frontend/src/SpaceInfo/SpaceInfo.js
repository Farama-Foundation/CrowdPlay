import PropTypes from 'prop-types'
import { Descriptions } from 'antd'
import {
  isBox, isDict, isDiscrete, isMultiDiscrete,
} from '../utils'

export default function SpaceInfo({ type, space }) {
  const columns = isMultiDiscrete(space.name) ? 4 : 3

  return (
    <Descriptions
      bordered
      column={columns}
      layout="vertical"
      title={`${type} Space`}
      size="small"
    >
      <Descriptions.Item label="Name">{space.name}</Descriptions.Item>
      <Descriptions.Item label="dType">{space.dtype}</Descriptions.Item>

      {isDiscrete(space.name) && (
        <Descriptions.Item label="N">{space.n}</Descriptions.Item>
      )}

      {isBox(space.name) && (
        <Descriptions.Item label="Shape">
          (
          {space.shape.join(', ')}
          )
        </Descriptions.Item>
      )}

      {isMultiDiscrete(space.name) && (
        <>
          <Descriptions.Item label="NVec">
            (
            {space.nvec.join(', ')}
            )
          </Descriptions.Item>
          <Descriptions.Item label="Shape">
            (
            {space.shape.join(', ')}
            )
          </Descriptions.Item>
        </>
      )}

      {isDict(space.name) && (
        <Descriptions.Item label="Space">TODO</Descriptions.Item>
      )}
    </Descriptions>
  )
}

SpaceInfo.propTypes = {
  type: PropTypes.string.isRequired,
  space: PropTypes.object.isRequired,
}

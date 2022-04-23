import PropTypes from 'prop-types'

export default function If(props) {
  const {
    condition,
    thenBlock,
    elseBlock,
    children,
  } = props

  const cond = typeof condition === 'function' ? condition() : condition

  if (cond) {
    if (thenBlock) {
      return typeof thenBlock === 'function' ? thenBlock() : thenBlock
    }
    return children
  }
  
  if (elseBlock) {
    return typeof elseBlock === 'function' ? elseBlock() : elseBlock
  }

  return null
}

If.propTypes = {
  children: PropTypes.node,
  condition: PropTypes.oneOfType([PropTypes.func, PropTypes.bool]).isRequired,
  thenBlock: PropTypes.oneOfType([PropTypes.func, PropTypes.node]),
  elseBlock: PropTypes.oneOfType([PropTypes.func, PropTypes.node]),
}

If.defaultProps = {
  children: null,
  thenBlock: null,
  elseBlock: null,
}

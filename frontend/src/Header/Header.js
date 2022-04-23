import './Header.less'
import { Layout, Typography } from 'antd'
import PropTypes from 'prop-types'
import GetTokenButton from './GetTokenButton'

const { Title } = Typography

export default function Header(props) {
  const { include_buttons } = props
  return (
    <Layout.Header className="Header">
      <Title className="title">CrowdPlay</Title>

      {include_buttons && (
        <div className="buttonsdiv">
          <GetTokenButton />
        </div>
      ) }

    </Layout.Header>
  )
}

Header.propTypes = {
  include_buttons: PropTypes.bool,
}

Header.defaultProps = {
  include_buttons: false,
}

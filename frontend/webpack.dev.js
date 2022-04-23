const path = require('path')
const { merge } = require('webpack-merge')
const common = require('./webpack.common.js')

const devHost = process.env.DEV_HOST || 'localhost'
const devPort = process.env.DEV_PORT || 9000
const proxyTarget = process.env.PROXY_TARGET || 'http://localhost:5000'

module.exports = merge(common, {
  mode: 'development',
  devtool: 'inline-source-map',
  devServer: {
    contentBase: './dist',
    host: devHost,
    port: devPort,
    historyApiFallback: true,
    proxy: {
      '/api': {
        changeOrigin: true,
        secure: false,
        target: proxyTarget
      },
      '/socket.io': {
        secure: false,
        ws: true,
        target: proxyTarget
      }
    }
  }
})

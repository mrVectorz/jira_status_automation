module.exports = {
  style: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer'),
      ],
    },
  },
  devServer: {
    // Fix WebSocket connection issues for hot module replacement
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws',
    },
    webSocketServer: {
      type: 'ws',
      options: {
        host: '0.0.0.0',
        port: 'auto',
      },
    },
    // Allow connections from any origin (for development)
    allowedHosts: 'all',
    // Ensure hot reloading works properly
    hot: true,
    liveReload: true,
  },
}


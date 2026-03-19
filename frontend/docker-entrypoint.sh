#!/bin/sh
echo "window._env_ = { API_URL: '${API_URL}' };" > /usr/share/nginx/html/env-config.js
exec "$@"

module.exports = {
  apps : [{
    name: 'gprimebot',
    script: 'start.sh',

    // Options reference: https://pm2.keymetrics.io/docs/usage/application-declaration/
    instances: 1,
    autorestart: false,
    watch: false,
    max_memory_restart: '1G',
  }]
};

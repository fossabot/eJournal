const yaml = require('js-yaml');
const fs = require('fs');

const supportedBrowsers = yaml.safeLoad(fs.readFileSync('../../config/supported-browsers.yml', 'utf8'))

module.exports = supportedBrowsers

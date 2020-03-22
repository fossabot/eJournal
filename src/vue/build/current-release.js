const fs = require('fs')

const packageJSON = fs.readFileSync('./package.json')
const version = JSON.parse(packageJSON).version || 'version unknown'

const currentRelease = {
    version,
}

module.exports = currentRelease

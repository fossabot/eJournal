import axios from 'axios'

axios.defaults.baseURL = CustomEnv.API_URL

const conn = axios.create()

// An instance without refresh interceptor
const connRefresh = axios.create()

const connUpFile = axios.create({
    headers: {
        'Content-Type': 'multipart/form-data',
    },
})

const connDownFile = axios.create({
    responseType: 'arraybuffer',
    headers: {
        'Content-Type': 'multipart/form-data',
    },
})

const connSentry = axios.create({
    /* /api/0/projects/{organization_slug}/{project_slug}/ */
    baseURL: `https://${CustomEnv.SENTRY_BASE_URL}/api/projects/${CustomEnv.SENTRY_ORGANIZATION_SLUG}/${CustomEnv.SENTRY_PROJECT_SLUG}/`, // eslint-disable-line
    headers: {
        Authorization: `DSN ${CustomEnv.SENTRY_DSN}`,
    },
})

export default {
    conn,
    connRefresh,
    connUpFile,
    connDownFile,
    connSentry,
}

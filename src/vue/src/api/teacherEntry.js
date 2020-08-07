import auth from '@/api/auth.js'

export default {
    get (id, connArgs = auth.DEFAULT_CONN_ARGS) {
        return auth.get(`teacher_entries/${id}`, null, connArgs)
            .then(response => response.data.entry)
    },

    create (data, connArgs = auth.DEFAULT_CONN_ARGS) {
        return auth.create('teacher_entries', data, connArgs)
            .then(response => response.data.teacher_entry)
    },
}

<template>
    <b-form-file
        :accept="acceptedFiletype"
        :state="Boolean(file)"
        :placeholder="placeholderText"
        class="fileinput"
        @change="fileHandler"
    />
</template>

<script>
import auth from '@/api/auth.js'

export default {
    props: {
        acceptedFiletype: {
            required: true,
            String,
        },
        maxSizeBytes: {
            required: true,
            Number,
        },
        aID: {
            required: true,
            String,
        },
        autoUpload: {
            default: false,
            Boolean,
        },
        endpoint: {
            default: 'files',
        },
        placeholder: {
            default: 'No file chosen',
        },
        contentID: {
            default: null,
        },
    },
    data () {
        return {
            placeholderText: 'No file chosen',
            file: null,
        }
    },
    created () {
        // Assume the given file is present in the backend
        if (this.placeholder !== null && this.placeholder !== 'No file chosen') {
            this.file = true
            this.placeholderText = this.placeholder
        }
    },
    methods: {
        fileHandler (e) {
            const files = e.target.files

            if (!files.length) { return }
            if (files[0].size > this.maxSizeBytes) {
                this.$toasted.error(`The selected file exceeds the maximum file size of: ${this.maxSizeBytes} bytes.`)
                return
            }

            this.file = files[0]

            this.$emit('fileSelect', this.file.file_name)

            if (this.autoUpload) { this.uploadFile() }
        },
        uploadFile () {
            const formData = new FormData()
            formData.append('file', this.file)
            formData.append('assignment_id', this.aID)
            formData.append('content_id', this.contentID)
            this.$emit('uploadingFile')
            auth.uploadFile(this.endpoint, formData, { customSuccessToast: 'File upload success.' })
                .then((resp) => {
                    this.$emit('fileUploadSuccess', resp.data)
                })
                .catch(() => {
                    this.$emit('fileUploadFailed', this.file.file_name)
                    this.file = null
                })
        },
    },
}
</script>

<template>
    <div
        class="file-controls"
        @click="fileDownload"
    >
        <icon
            name="download"
            class="shift-up-2"
        />
        <b class="ml-1">
            {{ file.file_name }}
        </b>
    </div>
</template>

<script>
import auth from '@/api/auth.js'

export default {
    props: {
        file: {
            required: true,
        },
    },
    methods: {
        fileDownload () {
            auth.downloadFile(this.file.download_url)
                .then((response) => {
                    try {
                        const blob = new Blob([response.data], { type: response.headers['content-type'] })
                        const link = document.createElement('a')
                        link.href = window.URL.createObjectURL(blob)
                        link.download = this.file.file_name
                        document.body.appendChild(link)
                        link.click()
                        link.remove()
                    } catch (_) {
                        this.$toasted.error('Error creating file.')
                    }
                })
        },
    },
}
</script>

<style lang="sass">
.file-controls
    &:hover
        cursor: pointer
    b
        text-decoration: underline !important
</style>

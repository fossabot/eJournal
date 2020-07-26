<template>
    <div>
        <div class="mb-1">
            <theme-select
                v-model="selectedJournals"
                label="name"
                trackBy="id"
                :options="assignmentJournals"
                :multiple="true"
                :searchable="true"
                placeholder="Select Journals"
            />
            <small v-if="!showUsernameInput">
                Or
                <span
                    class="text-blue cursor-pointer"
                    @click="showUsernameInput = true"
                >
                    select by username</span>.
            </small>
            <b-input
                v-else
                v-model="usernameInput"
                class="theme-input  mt-2 mb-2"
                placeholder="Enter a username and press enter to select"
                @keydown.enter.native="selectUsername"
            />
        </div>
        <theme-select
            v-if="templates && templates.length > 0"
            v-model="selectedTemplate"
            label="name"
            trackBy="id"
            :options="templates"
            :multiple="false"
            :searchable="true"
            placeholder="Select A Template"
        />
        <span v-else>
            No templates for this assignment. Create some in the assignment editor first.
        </span>
        <template v-if="selectedTemplate">
            <hr/>
            <entry-preview
                ref="entry-prev"
                :template="selectedTemplate"
                :nID="-1"
                :jID="selectedJournalIDs"
                @posted="entryPosted"
            />
        </template>

        <div v-if="false">
            <b class="text-red">Errors in file:</b>
            <div
                v-if="errorLogs.non_participants || errorLogs.unknown_users"
                class="text-dark-grey mb-1"
            >
                <i>Note: it is likely that one or more of the users reported as unknown or non participant still need
                    to visit this assignment on the LMS (Canvas).</i>
            </div>
            <b
                v-if="errorLogs.general"
                class="mb-1"
            >
                {{ errorLogs.general }}
            </b>
            <div
                v-if="errorLogs.unknown_users"
                class="mb-1"
            >
                <b>The following users do not exist:</b><br/>
                <span
                    v-for="(username, lineNumber) in errorLogs.unknown_users"
                    :key="`unknown-users-${lineNumber}-${username}`"
                >
                    <b>&emsp;&emsp;&emsp;{{ lineNumber }})</b> {{ username }}<br/>
                </span>
            </div>
            <div
                v-if="errorLogs.non_participants"
                class="mb-1"
            >
                <b>The following users are not participants of the assignment:</b><br/>
                <span
                    v-for="(username, lineNumber) in errorLogs.non_participants"
                    :key="`non_participants-${lineNumber}-${username}`"
                >
                    <b>&emsp;&emsp;&emsp;{{ lineNumber }})</b> {{ username }}<br/>
                </span>
            </div>
            <div
                v-if="errorLogs.incorrect_format_lines"
                class="mb-1"
            >
                <b>The following lines are incorrectly formatted:</b><br/>
                <span
                    v-for="(content, lineNumber) in errorLogs.incorrect_format_lines"
                    :key="`incorrect-format-${lineNumber}-${content}`"
                >
                    <b>&emsp;&emsp;&emsp;{{ lineNumber }})</b> {{ content }}<br/>
                </span>
            </div>
            <div v-if="errorLogs.duplicates">
                <b>The following users occur twice:</b><br/>
                <span
                    v-for="(username, lineNumber) in errorLogs.duplicates"
                    :key="`duplicates-${lineNumber}-${username}`"
                >
                    <b>&emsp;&emsp;&emsp;{{ lineNumber }})</b> {{ username }}<br/>
                </span>
            </div>
        </div>
    </div>
</template>

<script>
import EntryPreview from '@/components/entry/EntryPreview.vue'

import auth from '@/api/auth.js'
import assignmentAPI from '@/api/assignment.js'

export default {
    components: {
        EntryPreview,
    },
    props: {
        aID: {
            required: true,
        },
        assignmentJournals: {
            required: true,
        },
    },
    data () {
        return {
            placeholderText: 'No file chosen',
            selectedJournals: [],
            selectedTemplate: null,
            templates: null,
            showUsernameInput: false,
            usernameInput: null,
        }
    },
    computed: {
        selectedJournalIDs () {
            return this.selectedJournals.map(journal => journal.id)
        },
    },
    created () {
        assignmentAPI.getTemplates(this.aID)
            .then((templates) => {
                this.templates = templates
            })
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
            this.resetErrorLogs()

            this.$emit('fileSelect', this.file.name)

            if (this.autoUpload) { this.uploadFile() }
        },
        uploadFile () {
            const formData = new FormData()
            formData.append('file', this.file)
            formData.append('assignment_id', this.aID)
            formData.append('content_id', this.contentID)

            auth.uploadFile(this.endpoint, formData, {
                customSuccessToast: 'Successfully imported bonus points.',
                customErrorToast: 'Something is wrong with the uploaded file.',
            })
                .then(() => {
                    this.$emit('bonusPointsSuccesfullyUpdated', this.file.name)
                    this.file = null
                    this.$refs.bonusInput.reset()
                })
                .catch((error) => {
                    this.$emit('bonusPointsFileFormatIssues', this.file.name)
                    this.file = null
                    this.$refs.bonusInput.reset()
                    this.errorLogs = error.response.data.description
                })
        },
        resetErrorLogs () {
            this.errorLogs = null
        },
        selectUsername () {
            // Split input on comma and space
            this.usernameInput.split(/[ ,]+/).forEach((username) => {
                const journalFromUsername = this.assignmentJournals.find(journal => journal.usernames.split(', ')
                    .some(journalUsername => journalUsername === username))

                if (!journalFromUsername) {
                    this.$toasted.error(`${username} does not exist!`)
                } else if (!this.selectedJournals.includes(journalFromUsername)) {
                    this.selectedJournals.push(journalFromUsername)
                }
            })

            this.usernameInput = null
        },
        entryPosted () {

        },
    },
}
</script>

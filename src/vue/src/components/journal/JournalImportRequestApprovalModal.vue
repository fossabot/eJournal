<template>
    <b-modal
        :id="modalID"
        :ref="modalID"
        size="lg"
        title="Manage Import Requests"
        hideFooter
        noEnforceFocus
    >
        <b-card class="no-hover">
            <h2 class="theme-h2 multi-form">
                Select an import request
            </h2>

            <p>
                An approved import request will add all entries to the timeline, how grades are handled can be selected
                below. Please note that any related comments will also be imported.
            </p>

            <load-wrapper
                :loading="loading"
            >
                <b-card
                    v-for="(jir, i) in jirs"
                    :key="`jir-display-${jir.id}`"
                    :class="{'active': selectedJir === jir.id}"
                    @click="selectedJir = jir.id"
                >
                    <h4>{{ jir.source.assignment.name }}</h4>
                    <div v-if="selectedJir === jir.id">
                        <journal-card
                            v-b-tooltip.hover="'Navigate to journal in full'"
                            :journal="jir.source.journal"
                            :assignment="jir.source.assignment"
                            @click.native="$router.push({
                                name: 'Journal',
                                params: {
                                    cID: jir.source.assignment.course.id,
                                    aID: jir.source.assignment.id,
                                    jID: jir.source.journal.id
                                },
                                target: '_blank',
                            })"
                            @journal-deleted="journalDeleted(journal)"
                        />
                        <b-button
                            :class="{'multi-form': selectedPreview === jir.id}"
                            @click="selectedPreview = (selectedPreview === jir.id) ? null : jir.id"
                        >
                            {{ (selectedPreview === jir.id) ? 'Hide journal preview' : 'Show journal preview' }}
                        </b-button>
                        <div
                            v-if="selectedPreview === jir.id"
                            class="resp-iframe-container"
                        >
                            <iframe
                                class="resp-iframe"
                                :src="jirToJournalUrl(jir)"
                                title="description"
                            />
                        </div>

                        <hr/>

                        <h5>How should the import request be processed?</h5>

                        <b-form-select
                            v-model="jirAction"
                            :selectSize="1"
                            class="theme-select multi-form"
                        >
                            <option value="grades">
                                Import including grades
                            </option>
                            <option value="no-grades">
                                Import excluding grades
                            </option>
                            <option value="decline">
                                Decline
                            </option>
                        </b-form-select>

                        <b-button
                            v-if="jirAction"
                            type="submit"
                            @click="handleJIR(jir, i)"
                        >
                            <icon name="paper-plane"/>
                            Submit
                        </b-button>
                    </div>
                </b-card>
            </load-wrapper>
        </b-card>
    </b-modal>
</template>

<script>
import loadWrapper from '@/components/loading/LoadWrapper.vue'
import journalCard from '@/components/assignment/JournalCard.vue'

import journalImportRequestAPI from '@/api/journal_import_request.js'

export default {
    components: {
        loadWrapper,
        journalCard,
    },
    props: {
        modalID: {
            required: true,
            type: String,
        },
    },
    data () {
        return {
            jirs: [],
            selectedJir: null,
            selectedPreview: null,
            loading: true,
            jirAction: null,
        }
    },
    computed: {
    },
    created () {
        journalImportRequestAPI.list(this.$route.params.jID).then((jirs) => {
            this.jirs = jirs
            this.loading = false
        })
    },
    methods: {
        jirToJournalUrl (jir) {
            return 'http://localhost:8080/Home/'
                + `Course/${jir.source.assignment.course.id}/`
                + `Assignment/${jir.source.assignment.id}/`
                + `Journal/${jir.source.journal.id}`
        },
        handleJIR (jir, i) {
            // TODO are you sure, send to backend
            this.$delete(this.jirs, i)
        },
    },
}
</script>

<style lang="sass">
.resp-iframe-container
    position: relative
    overflow: hidden
    padding-top: 56.25%

.resp-iframe
    position: absolute
    top: 0
    left: 0
    width: 100%
    height: 100%
    border: 0
</style>

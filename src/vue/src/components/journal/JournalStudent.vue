<template>
    <b-row class="outer-container" no-gutters>
        <b-col md="12" lg="8" xl="9" class="inner-container-edag-page">
            <b-col md="12" lg="auto" xl="4" class="left-content-edag-page">
                <bread-crumb v-if="$root.lgMax()" class="main-content">&nbsp;</bread-crumb>
                <edag @select-node="selectNode" :selected="currentNode" :nodes="nodes"/>
            </b-col>

            <b-col md="12" lg="auto" xl="8" class="main-content-edag-page">
                <bread-crumb v-if="$root.xl()" class="main-content">&nbsp;</bread-crumb>
                <div v-if="nodes.length > currentNode">
                    <div v-if="nodes[currentNode].type == 'e'">
                        <entry-node
                            ref="entry-template-card"
                            @edit-node="adaptData"
                            :cID="cID"
                            :entryNode="nodes[currentNode]"/>
                    </div>
                    <div v-else-if="nodes[currentNode].type == 'd'">
                        <div v-if="nodes[currentNode].entry !== null">
                            <entry-node :cID="cID" ref="entry-template-card" @edit-node="adaptData" :entryNode="nodes[currentNode]"/>
                        </div>
                        <div v-else>
                            <entry-preview v-if="checkDeadline()" ref="entry-template-card" @content-template="fillDeadline" :template="nodes[currentNode].template" :cID="cID"/>
                            <b-card v-else class="no-hover" :class="$root.getBorderClass($route.params.cID)">
                                <h2 class="mb-2">{{nodes[currentNode].template.name}}</h2>
                                <b>The deadline has passed. You can not submit an entry anymore.</b>
                            </b-card>
                        </div>
                    </div>
                    <div v-else-if="nodes[currentNode].type == 'a'">
                        <add-card @info-entry="addNode" :addNode="nodes[currentNode]"/>
                    </div>
                    <div v-else-if="nodes[currentNode].type == 'p'">
                        <b-card class="no-hover" :class="getProgressBorderClass()">
                            <h2 class="mb-2">Progress: {{ nodes[currentNode].target }} points</h2>
                            <span v-if="progressPointsLeft > 0">
                                <b>{{ progressNodes[nodes[currentNode].nID] }}</b> out of <b>{{ nodes[currentNode].target }}</b> points.<br/>
                                <b>{{ progressPointsLeft }}</b> more required before <b>{{ $root.beautifyDate(nodes[currentNode].deadline) }}</b>.
                            </span>
                        </b-card>
                    </div>
                </div>
            </b-col>
        </b-col>

        <b-col md="12" lg="4" xl="3" class="right-content-edag-page right-content">
            <b-row>
                <b-col md="6" lg="12">
                    <h3>Description</h3>
                    <b-card class="no-hover" :class="$root.getBorderClass($route.params.cID)">
                        <div v-html="assignmentDescription"/>
                    </b-card>
                </b-col>
                <b-col md="6" lg="12">
                    <h3>Progress</h3>
                    <b-card class="no-hover" :class="$root.getBorderClass($route.params.cID)">
                        <progress-bar v-if="journal.stats" :currentPoints="journal.stats.acquired_points" :totalPoints="journal.stats.total_points"/>
                    </b-card>
                </b-col>
            </b-row>
        </b-col>
    </b-row>
</template>

<script>
import contentColumns from '@/components/columns/ContentColumns.vue'
import entryNode from '@/components/entry/EntryNode.vue'
import entryPreview from '@/components/entry/EntryPreview.vue'
import addCard from '@/components/journal/AddCard.vue'
import edag from '@/components/edag/Edag.vue'
import breadCrumb from '@/components/assets/BreadCrumb.vue'
import progressBar from '@/components/assets/ProgressBar.vue'
import journalApi from '@/api/journal'
import assignmentApi from '@/api/assignment.js'

export default {
    props: ['cID', 'aID', 'jID'],
    data () {
        return {
            currentNode: 0,
            editedData: ['', ''],
            nodes: [],
            journal: {},
            progressNodes: {},
            progressPointsLeft: 0,
            assignmentDescription: ''
        }
    },
    created () {
        journalApi.get_nodes(this.jID)
            .then(data => {
                this.nodes = data.nodes
                if (this.$route.query.nID !== undefined) {
                    this.currentNode = this.findEntryNode(parseInt(this.$route.query.nID))
                }

                for (var node of this.nodes) {
                    if (node.type === 'p') {
                        this.progressPoints(node)
                    }
                }
            })
            .catch(error => { this.$toasted.error(error.response.data.description) })

        journalApi.get_journal(this.jID)
            .then(data => {
                this.journal = data.journal
            })
            .catch(_ => this.$toasted.error('Error while loading journal data.'))

        assignmentApi.get_assignment_data(this.cID, this.aID)
            .then(data => {
                this.assignmentDescription = data.description
            })
            .catch(_ => this.$toasted.error('Error while loading assignment description.'))
    },
    watch: {
        currentNode: function () {
            if (this.nodes[this.currentNode].type === 'p') {
                this.progressPoints(this.nodes[this.currentNode])
                this.progressPointsLeft = this.nodes[this.currentNode].target - this.progressNodes[this.nodes[this.currentNode].nID]
            }
        }
    },
    methods: {
        adaptData (editedData) {
            this.nodes[this.currentNode] = editedData
            journalApi.create_entry(this.jID, this.nodes[this.currentNode].entry.template.tID, editedData.entry.content, this.nodes[this.currentNode].nID)
                .then(data => {
                    this.nodes = data.nodes
                    this.currentNode = data.added
                })
                .catch(error => { this.$toasted.error(error.response.data.description) })
        },
        selectNode ($event) {
            /* Function that prevents you from instant leaving an EntryNode
             * or a DeadlineNode when clicking on a different node in the
             * timeline. */
            if ($event === this.currentNode) {
                return this.currentNode
            }

            if (this.nodes[this.currentNode].type !== 'e' || this.nodes[this.currentNode].type !== 'd') {
                this.currentNode = $event
                return
            }

            if (this.$refs['entry-template-card'].saveEditMode === 'Save') {
                if (!confirm('Progress will not be saved if you leave. Do you wish to continue?')) {
                    return
                }
            }

            this.$refs['entry-template-card'].cancel()
            this.currentNode = $event
        },
        addNode (infoEntry) {
            journalApi.create_entry(this.jID, infoEntry[0].tID, infoEntry[1])
                .then(data => {
                    this.nodes = data.nodes
                    this.currentNode = data.added
                })
                .catch(error => { this.$toasted.error(error.response.data.description) })
        },
        fillDeadline (data) {
            journalApi.create_entry(this.jID, this.nodes[this.currentNode].template.tID, data, this.nodes[this.currentNode].nID)
                .then(data => {
                    this.nodes = data.nodes
                    this.currentNode = data.added
                })
                .catch(error => { this.$toasted.error(error.response.data.description) })
        },
        progressPoints (progressNode) {
            /* The function will update a given progressNode by
             * going through all the nodes and count the published grades
             * so far. */
            var tempProgress = 0
            for (var node of this.nodes) {
                if (node.nID === progressNode.nID) {
                    break
                }

                if (node.type === 'e' || node.type === 'd') {
                    if (node.entry && node.entry.grade && node.entry.grade !== '0') {
                        tempProgress += parseInt(node.entry.grade)
                    }
                }
            }

            this.progressNodes[progressNode.nID] = tempProgress
        },
        getProgressBorderClass () {
            return this.progressPointsLeft > 0 ? 'red-border' : 'green-border'
        },
        findEntryNode (nodeID) {
            for (var i = 0; i < this.nodes.length; i++) {
                if (this.nodes[i].nID === nodeID) {
                    return i
                }
            }
            return 0
        },
        checkDeadline () {
            var currentDate = new Date()
            var deadline = new Date(this.nodes[this.currentNode].deadline)

            return currentDate <= deadline
        }
    },
    components: {
        'content-columns': contentColumns,
        'bread-crumb': breadCrumb,
        'add-card': addCard,
        edag,
        'entry-node': entryNode,
        'entry-preview': entryPreview,
        'progress-bar': progressBar
    }
}
</script>
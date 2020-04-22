<!--
    Component that will show all the comments of a given entry and support
    the possibility to add comments when the right permissions are met.
-->
<template>
    <div>
        <div v-if="commentObject">
            <div
                v-for="(comment, index) in commentObject"
                :key="`comment-${eID}-${index}`"
                class="comment-section"
            >
                <img
                    :src="comment.author.profile_picture"
                    class="theme-img profile-picture-sm no-hover"
                />
                <b-card
                    :class="$root.getBorderClass($route.params.cID)"
                    class="no-hover comment-card"
                >
                    <div v-if="!editCommentStatus[index]">
                        <sandboxed-iframe :content="comment.text"/>
                        <hr class="full-width"/>
                        <b>{{ comment.author.full_name }}</b>
                        <icon
                            v-if="comment.can_edit"
                            name="trash"
                            class="float-right trash-icon"
                            @click.native="deleteComment(comment.id)"
                        />
                        <icon
                            v-if="comment.can_edit"
                            name="edit"
                            scale="1.07"
                            class="float-right ml-2 edit-icon"
                            @click.native="editCommentView(index, true, comment.text)"
                        />
                        <span
                            v-if="comment.published
                                && $root.beautifyDate(comment.last_edited)
                                    === $root.beautifyDate(comment.creation_date)"
                            class="timestamp"
                        >
                            {{ $root.beautifyDate(comment.creation_date) }}<br/>
                        </span>
                        <span
                            v-else-if="comment.published"
                            v-b-tooltip:hover="`Last edit by: ${comment.last_edited_by}`"
                            class="timestamp"
                        >
                            Last edited: {{ $root.beautifyDate(comment.last_edited) }}
                        </span>
                        <span
                            v-else
                            class="timestamp"
                        >
                            <icon
                                name="hourglass-half"
                                scale="0.8"
                            />
                            Will be published along with grade<br/>
                        </span>
                    </div>
                    <div v-else>
                        <text-editor
                            :id="'comment-text-editor-' + index"
                            :key="'comment-text-editor-' + index"
                            v-model="editCommentTemp[index]"
                            :basic="true"
                            :footer="false"
                            class="multi-form"
                        />
                        <b-button
                            v-if="comment.can_edit"
                            class="multi-form delete-button"
                            @click="editCommentView(index, false, '')"
                        >
                            <icon name="ban"/>
                            Cancel
                        </b-button>
                        <b-button
                            v-if="comment.can_edit"
                            :class="{ 'input-disabled': saveRequestInFlight }"
                            class="ml-2 add-button float-right"
                            @click="editComment(comment.id, index)"
                        >
                            <icon name="save"/>
                            Save
                        </b-button>
                    </div>
                </b-card>
            </div>
        </div>
        <div
            v-if="$hasPermission('can_comment')"
            class="comment-section"
        >
            <img
                :src="$store.getters['user/profilePicture']"
                class="theme-img profile-picture-sm no-hover"
            />
            <b-card
                :class="$root.getBorderClass($route.params.cID)"
                class="no-hover new-comment"
            >
                <text-editor
                    :id="`comment-text-editor-new-comment-${eID}`"
                    :key="`comment-text-editor-new-comment-${eID}`"
                    ref="comment-text-editor-ref"
                    v-model="tempComment"
                    :basic="true"
                    :footer="false"
                    placeholder="Type here to leave a comment"
                />
                <dropdown-button
                    v-if="$hasPermission('can_grade') && !entryGradePublished"
                    :up="true"
                    :selectedOption="$store.getters['preferences/saved'].comment_button_setting"
                    :options="{
                        p: {
                            text: 'Send',
                            icon: 'paper-plane',
                            class: '',
                        },
                        s: {
                            text: 'Send & publish after grade',
                            icon: 'paper-plane',
                            class: '',
                        },
                        g: {
                            text: 'Send & publish grade',
                            icon: 'paper-plane',
                            class: '',
                        },
                    }"
                    :class="{ 'input-disabled': saveRequestInFlight }"
                    class="float-right mt-2"
                    @click="addComment"
                    @change-option="changeButtonOption"
                />
                <b-button
                    v-else
                    :class="{ 'input-disabled': saveRequestInFlight }"
                    class="float-right mt-2"
                    @click="addComment('p')"
                >
                    <icon name="paper-plane"/>
                    Send
                </b-button>
            </b-card>
        </div>
    </div>
</template>

<script>
import dropdownButton from '@/components/assets/DropdownButton.vue'
import textEditor from '@/components/assets/TextEditor.vue'
import sandboxedIframe from '@/components/assets/SandboxedIframe.vue'

import commentAPI from '@/api/comment.js'

export default {
    components: {
        dropdownButton,
        textEditor,
        sandboxedIframe,
    },
    props: {
        eID: {
            required: true,
        },
        journal: {
            required: true,
        },
        entryGradePublished: {
            type: Boolean,
            default: false,
        },
    },
    data () {
        return {
            tempComment: '',
            commentObject: null,
            editCommentStatus: [],
            editCommentTemp: [],
            saveRequestInFlight: false,
        }
    },
    watch: {
        eID () {
            this.tempComment = ''
            this.getComments()
        },
        entryGradePublished () {
            this.getComments()
        },
    },
    created () {
        this.setComments()
    },
    methods: {
        setComments () {
            commentAPI.getFromEntry(this.eID)
                .then((comments) => {
                    this.commentObject = comments
                    for (let i = 0; i < this.commentObject.length; i++) {
                        this.editCommentStatus.push(false)
                        this.editCommentTemp.push('')
                    }
                })
        },
        getComments () {
            commentAPI.getFromEntry(this.eID)
                .then((comments) => { this.commentObject = comments })
        },
        changeButtonOption (option) {
            this.$store.commit('preferences/CHANGE_PREFERENCES', { comment_button_setting: option })
        },
        addComment (option) {
            if (this.tempComment !== '') {
                if (option === 'g') {
                    this.$emit('publish-grade')
                }

                this.saveRequestInFlight = true
                commentAPI.create({
                    entry_id: this.eID,
                    text: this.tempComment,
                    published: option === 'p' || option === 'g',
                })
                    .then((comment) => {
                        this.saveRequestInFlight = false
                        this.commentObject.push(comment)
                        for (let i = 0; i < this.commentObject.length; i++) {
                            this.editCommentStatus.push(false)
                            this.editCommentTemp.push('')
                        }
                        this.tempComment = ''
                        this.$refs['comment-text-editor-ref'].clearContent()
                    })
                    .catch(() => { this.saveRequestInFlight = false })
            }
        },
        editCommentView (index, status, text) {
            if (status) {
                this.$set(this.editCommentTemp, index, text)
            }

            this.$set(this.editCommentStatus, index, status)
        },
        editComment (cID, index) {
            this.saveRequestInFlight = true
            commentAPI.update(cID, {
                text: this.editCommentTemp[index],
            })
                .then((comment) => {
                    this.saveRequestInFlight = false
                    this.$set(this.commentObject, index, comment)
                    this.$set(this.editCommentStatus, index, false)
                })
                .catch(() => {
                    this.saveRequestInFlight = false
                })
        },
        deleteComment (cID) {
            if (window.confirm('Are you sure you want to delete this comment?')) {
                commentAPI.delete(cID, { responseSuccessToast: true })
                    .then(() => {
                        this.commentObject.forEach((comment, i) => {
                            if (comment.id === cID) {
                                this.commentObject.splice(i, 1)
                            }
                        })
                        this.commentObject.forEach(() => {
                            this.editCommentStatus.push(false)
                            this.editCommentTemp.push('')
                        })
                    })
            }
        },
    },
}
</script>

<style lang="sass">
.comment-section
    display: flex
    .profile-picture-sm
        margin: 0px 12px
        display: inline
    .new-comment.card-body
        display: flex
        flex-wrap: wrap
    .card
        flex: 1 1 auto
        overflow: hidden
    .comment-card
        .card-body
            padding-bottom: 5px
            .trash-icon, .edit-icon
                margin-top: 4px
                margin-left: 4px
</style>

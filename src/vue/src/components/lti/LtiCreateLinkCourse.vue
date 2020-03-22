<template>
    <div v-if="courses">
        <h2 class="theme-h2 multi-form">
            Configuring a Course
        </h2>
        <span class="d-block mb-2">
            You came here from a learning environment through an unconfigured
            course. Do you want to create a new course on eJournal,
            or link it to an existing one?
        </span>
        <b-card class="no-hover">
            <b-button
                class="add-button big-button-text full-width"
                @click="showModal('createCourseRef')"
            >
                <icon
                    name="plus-square"
                    class="mr-3"
                    scale="1.8"
                />
                Create new course
            </b-button>
            <hr/>
            If you have not yet preconfigured this course on eJournal, click the button above
            to create a new course. This will be linked to your learning environment, allowing for automatic
            grade passback.
        </b-card>
        <b-card class="no-hover">
            <b-button
                class="change-button big-button-text full-width"
                @click="showModal('linkCourseRef')"
            >
                <icon
                    name="link"
                    class="mr-3"
                    scale="1.8"
                />
                Link to existing course
            </b-button>
            <hr/>
            If you have already set up a course on eJournal, you can link it to the course in
            your learning environment by clicking the button above.
        </b-card>

        <b-modal
            ref="createCourseRef"
            title="New Course"
            size="lg"
            hideFooter
            noEnforceFocus
        >
            <create-course
                :lti="lti"
                @handleAction="handleCreation"
            />
        </b-modal>

        <b-modal
            ref="linkCourseRef"
            title="Link Course"
            size="lg"
            hideFooter
            noEnforceFocus
        >
            <link-course
                :lti="lti"
                :courses="courses"
                @handleAction="handleLinked"
            />
        </b-modal>
    </div>
</template>

<script>
import createCourse from '@/components/course/CreateCourse.vue'
import linkCourse from '@/components/lti/LinkCourse.vue'

export default {
    name: 'LtiCreateLinkCourse',
    components: {
        createCourse,
        linkCourse,
    },
    props: ['lti', 'courses'],
    methods: {
        signal (msg) {
            this.$emit('handleAction', msg)
        },
        showModal (ref) {
            this.$refs[ref].show()
        },
        hideModal (ref) {
            this.$refs[ref].hide()
        },
        handleCreation (cID) {
            this.hideModal('createCourseRef')
            this.signal(['courseCreated', cID])
        },
        handleLinked (cID) {
            this.hideModal('linkCourseRef')
            this.signal(['courseLinked', cID])
        },
    },
}
</script>

import Vue from 'vue'
import Router from 'vue-router'
import Home from '@/views/Home'
import Journal from '@/views/Journal'
import Assignment from '@/views/Assignment'
import Course from '@/views/Course'
import Profile from '@/views/Profile'
import Guest from '@/views/Guest'
import Register from '@/views/Register'
import LtiLaunch from '@/views/LtiLaunch'
import CourseCreation from '@/views/CourseCreation'
import AssignmentsOverview from '@/views/AssignmentsOverview'

Vue.use(Router)

export default new Router({
    routes: [{
        path: '/',
        name: 'Guest',
        component: Guest
    }, {
        path: '/Home',
        name: 'Home',
        component: Home
    }, {
        path: '/Register',
        name: Register,
        component: Register
    }, {
        path: '/CourseCreation',
        name: 'CourseCreation',
        component: CourseCreation
    }, {
        path: '/Profile',
        name: 'Profile',
        component: Profile
    }, {
        path: '/AssignmentsOverview',
        name: 'AssignmentsOverview',
        component: AssignmentsOverview
    }, {
        path: '/Home/Course/:cID',
        name: 'Course',
        component: Course,
        props: true
    }, {
        path: '/Home/Course/:cID/Assignment/:aID',
        name: 'Assignment',
        component: Assignment,
        props: true
    }, {
        path: '/Home/Course/:cID/Assignment:aID/Journal/:jID',
        name: 'Journal',
        component: Journal,
        props: true
    }, {
        path: '/lti/launch',
        name: 'LtiLaunch',
        component: LtiLaunch
    }]
})
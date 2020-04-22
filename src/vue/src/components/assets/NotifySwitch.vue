<template>
    <div class="round-border">
        <b-button
            v-b-tooltip:hover="'Receive an email immediatly'"
            class="multi-form blue-button mr-2"
            :class="{'active': selected == 'p'}"
            @click="$emit('changedSelected', 'p')"
        >
            <icon name="bell"/>
        </b-button>
        <b-button
            v-b-tooltip:hover="'Receive an email at the beginning of each day'"
            class="multi-form blue-button mr-2"
            :class="{'active': selected == 'd'}"
            @click="$emit('changedSelected', 'd')"
        >
            <icon name="clock"/>
        </b-button>
        <b-button
            v-b-tooltip:hover="'Receive an email at the beginning of each week'"
            class="multi-form blue-button mr-2"
            :class="{'active': selected == 'w'}"
            @click="$emit('changedSelected', 'w')"
        >
            <icon name="calendar"/>
        </b-button>
        <b-button
            v-b-tooltip:hover="'Do not receive any emails'"
            class="multi-form mr-2"
            :class="{'active': selected == 'o'}"
            @click="$emit('changedSelected', 'o')"
        >
            <icon name="times"/>
        </b-button>
    </div>
</template>

<script>
export default {
    props: ['selected'],
    computed: {
        active: {
            get () {
                return this.selected
            },
            set (value) {
                this.$emit('changedSelected', value)
            },
        },
    },
}
</script>

<style lang="sass">
@import "~sass/modules/colors.sass"

.switch
    position: relative
    display: inline-block
    width: 48px
    height: 26px
    input
        display: none
    .slider
        position: absolute
        cursor: pointer
        top: 0
        left: 0
        right: 0
        bottom: 0
        background-color: #ccc
        -webkit-transition: .4s
        transition: .4s
        border-radius: 1em !important
        &:before
            position: absolute
            content: ""
            height: 18px
            width: 18px
            left: 4px
            bottom: 4px
            background-color: white
            -webkit-transition: .4s
            transition: .4s
            border-radius: 1em !important

input:checked + .slider
    background-color: $theme-green

input:focus + .slider
    box-shadow: 0 0 1px #2196F3

input:checked + .slider:before
    -webkit-transform: translateX(21px)
    -ms-transform: translateX(21px)
    transform: translateX(21px)
</style>

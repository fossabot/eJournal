<template>
    <b-card
        class="no-hover"
        :class="$root.getBorderClass($route.params.cID)"
    >
        <h2 class="theme-h2 multi-form">
            {{ assignment.name }}
        </h2>
        <sandboxed-iframe
            v-if="assignment.description"
            :content="assignment.description"
        />
        <hr class="full-width"/>
        <b v-if="assignment.unlock_date && new Date(assignment.unlock_date) > new Date()">
            This assignment is locked and will be made available later.<br/>
            Unlock date: {{ $root.beautifyDate(assignment.unlock_date) }}
        </b>
        <span v-else>
            <b v-if="assignment.due_date">
                <span v-if="new Date() > new Date(assignment.due_date) && !assignment.lock_date">
                    The due date for this assignment has passed.<br/>
                </span>
                Due date: {{ $root.beautifyDate(assignment.due_date) }}<br/>
            </b>
            <b v-if="assignment.lock_date">
                <span v-if="new Date(assignment.lock_date) < new Date()">
                    This assignment has been locked<br/>
                </span>
                Lock date: {{ $root.beautifyDate(assignment.lock_date) }}<br/>
            </b>
            <b v-if="assignment.points_possible">
                Points possible: {{ assignment.points_possible }}<br/>
            </b>
        </span>
    </b-card>
</template>

<script>
import sandboxedIframe from '@/components/assets/SandboxedIframe.vue'

export default {
    components: {
        sandboxedIframe,
    },
    props: ['assignment'],
}
</script>

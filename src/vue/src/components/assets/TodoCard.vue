<template>
    <b-card :class="$root.getBorderClass(deadline.id)">
        <!-- Teacher show things todo -->
        <number-badge
            v-if="deadline.stats && deadline.stats.needs_marking + deadline.stats.unpublished > 0"
            :leftNum="deadline.stats.needs_marking"
            :rightNum="deadline.stats.unpublished"
            class="float-right multi-form"
            :title="squareInfo"
        />

        <b class="field-heading">
            {{ deadline.name }}
        </b>
        ({{ course.abbreviation }})
        <b-badge
            v-if="!deadline.is_published"
            class="ml-2 align-top"
        >
            Unpublished
        </b-badge>
        <br/>
        <span v-if="deadline.deadline.date">
            <!-- Teacher deadline shows last submitted entry date  -->
            <span v-if="deadline.stats.needs_marking + deadline.stats.unpublished > 0">
                <icon
                    name="eye"
                    class="fill-grey shift-up-3"
                /> {{ timeLeft[1] }} ago<br/>
                <icon
                    name="flag"
                    class="fill-grey shift-up-3"
                /> {{ $root.beautifyDate(deadline.deadline.date) }}
            </span>
            <!-- Student deadline shows last not submitted deadline -->
            <span v-else>
                <icon
                    name="calendar"
                    class="fill-grey shift-up-3 mr-1"
                />
                <span v-if="timeLeft[0] < 0">Due in {{ timeLeft[1] }}<br/></span>
                <span
                    v-else
                    class="text-red"
                >{{ timeLeft[1] }} late<br/></span>
                <icon
                    name="flag"
                    class="fill-grey shift-up-3"
                /> {{ deadline.deadline.name }}
            </span>
        </span>
    </b-card>
</template>

<script>
import numberBadge from '@/components/assets/NumberBadge.vue'

export default {
    components: {
        numberBadge,
    },
    props: ['deadline', 'course'],
    computed: {
        timeLeft () {
            if (!this.deadline.deadline.date) { return '' }
            const dateNow = new Date()
            const dateFuture = new Date(this.deadline.deadline.date)

            // get total seconds between the times
            let delta = Math.abs(dateFuture - dateNow) / 1000
            const dir = dateNow - dateFuture

            // calculate (and subtract) whole days
            const days = Math.floor(delta / 86400)
            delta -= days * 86400

            // calculate (and subtract) whole hours
            const hours = Math.floor(delta / 3600) % 24
            delta -= hours * 3600

            // calculate (and subtract) whole minutes
            const minutes = Math.floor(delta / 60) % 60
            delta -= minutes * 60

            if (days) {
                return [dir, days > 1 ? `${days} days` : '1 day']
            }

            if (hours) {
                return [dir, hours > 1 ? `${hours} hours` : '1 hour']
            }

            return [dir, minutes > 1 ? `${minutes} minutes` : '1 minute']
        },
        squareInfo () {
            const info = []
            if (this.deadline.stats.needs_marking === 1) {
                info.push('an entry needs marking')
            } else if (this.deadline.stats.needs_marking > 1) {
                info.push(`${this.deadline.stats.needs_marking} entries need marking`)
            }
            if (this.deadline.stats.unpublished === 1) {
                info.push('an entry needs to be published')
            } else if (this.deadline.stats.unpublished > 1) {
                info.push(`${this.deadline.stats.unpublished} grades need to be published`)
            }
            const s = info.join(' and ')
            return `${s.charAt(0).toUpperCase()}${s.slice(1)}`
        },
    },
}
</script>

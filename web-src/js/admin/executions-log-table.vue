<template>
    <table class="highlight striped executions-log-table">
        <thead>
        <tr>
            <th class="start_time-column">Start Time</th>
            <th class="user-column">User</th>
            <th class="script-column">Script</th>
            <th class="status-column">Status</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="row in rows" :key="row.id" @click="rowClick(row)">
            <td>{{ row.startTimeString }}</td>
            <td>{{ row.user }}</td>
            <td>{{ row.script }}</td>
            <td>{{ row.fullStatus }}</td>
        </tr>
        </tbody>
    </table>
</template>

<script>
    export default {
        name: 'executions-log-table',
        props: {
            rows: Array,
            rowClick: {
                type: Function
            }
        }
    }
</script>

<style scoped>
    .executions-log-table tbody > tr {
        cursor: pointer;
    }

    .executions-log-table .start_time-column {
        width: 25%;
    }

    .executions-log-table .user-column {
        width: 25%;
    }

    .executions-log-table .script-column {
        width: 35%;
    }

    .executions-log-table .status-column {
        width: 15%;
    }
</style>
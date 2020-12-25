<template>
    <div class="executions-log-table">
        <table class="highlight striped">
            <thead>
            <tr>
                <th class="id-column">ID</th>
                <th class="start_time-column">Start Time</th>
                <th class="user-column">User</th>
                <th class="script-column">Script</th>
                <th class="status-column">Status</th>
            </tr>
            </thead>
            <tbody v-if="!loading">
            <tr :key="row.id" @click="rowClick(row)" v-for="row in rows">
                <td>{{ row.id }}</td>
                <td>{{ row.startTimeString }}</td>
                <td>{{ row.user }}</td>
                <td>{{ row.script }}</td>
                <td>{{ row.fullStatus }}</td>
            </tr>
            </tbody>
        </table>
        <p class="loading-text" v-if="loading">History will appear here</p>
    </div>
</template>

<script>
import {mapState} from 'vuex';

export default {
  name: 'executions-log-table',
  props: {
    rows: Array,
    rowClick: {
      type: Function
    }
  },
  computed: {
    ...mapState('history', ['loading'])
  }
}
</script>

<style scoped>
    .executions-log-table tbody > tr {
        cursor: pointer;
    }

    .executions-log-table .id-column {
        width: 10%;
    }

    .executions-log-table .start_time-column {
        width: 25%;
    }

    .executions-log-table .user-column {
        width: 25%;
    }

    .executions-log-table .script-column {
        width: 25%;
    }

    .executions-log-table .status-column {
        width: 15%;
    }

    .loading-text {
      color: var(--font-color-medium);
      font-size: 1.2em;
      text-align: center;
      margin-top: 1em;
    }
</style>
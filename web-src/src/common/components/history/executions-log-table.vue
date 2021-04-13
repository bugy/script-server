<template>
  <div class="executions-log-table">
    <table class="highlight striped">
      <thead>
      <tr>
        <th class="id-column">
          <a href="#" @click="sortBy('id')">ID</a>
        </th>
        <th class="start_time-column">
          <a href="#" @click="sortBy('startTimeString')">Start Time</a>
        </th>
        <th class="user-column">
          <a href="#" @click="sortBy('user')">User</a>
        </th>
        <th class="script-column">
          <a href="#" @click="sortBy('script')">Script</a>
        </th>
        <th class="status-column">
          <a href="#" @click="sortBy('fullStatus')">Status</a>
        </th>
      </tr>
      </thead>
      <tbody v-if="!loading">
      <tr v-for="row in rows" :key="row.id" @click="rowClick(row)">
        <td>{{ row.id }}</td>
        <td>{{ row.startTimeString }}</td>
        <td>{{ row.user }}</td>
        <td>{{ row.script }}</td>
        <td>{{ row.fullStatus }}</td>
      </tr>
      </tbody>
    </table>
    <p v-if="loading" class="loading-text">History will appear here</p>
  </div>
</template>

<script>
import {mapState} from 'vuex';

export default {
  name: 'executions-log-table',
  ascending: false,
  sortColumn: 'id',
  props: {
    rows: Array,
    rowClick: {
      type: Function
    }
  },

  methods: {
    sortBy: function sortBy(sortKey) {
      if (this.sortColumn === sortKey) {
        this.ascending = !this.ascending;
      } else {
        this.ascending = true;
        this.sortColumn = sortKey;
      }

      let ascending = this.ascending;

      this.rows.sort(function(a, b) {
        if (a[sortKey] > b[sortKey]) {
          return ascending ? 1 : -1
        } else if (a[sortKey] < b[sortKey]) {
          return ascending ? -1 : 1
        }
        return 0;
      })
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
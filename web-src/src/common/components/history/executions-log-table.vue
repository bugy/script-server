<template>
  <div class="executions-log-table">
    <table class="highlight striped">
      <thead>
      <tr>
        <th class="id-column" :class="showSort('id')" @click="sortBy('id')">ID</th>
        <th class="start_time-column" :class="showSort('startTimeString')" @click="sortBy('startTimeString')">Start Time</th>
        <th class="user-column" :class="showSort('user')" @click="sortBy('user')">User</th>
        <th class="script-column" :class="showSort('script')" @click="sortBy('script')">Script</th>
        <th class="status-column" :class="showSort('fullStatus')" @click="sortBy('fullStatus')">Status</th>
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
  props: {
    rows: Array,
    'sortColumn': {
      type: String,
      default: 'id'
    },
    'ascending': {
      type: Boolean,
      default: false
    },
    rowClick: {
      type: Function
    }
  },

  methods: {
    showSort: function (sortKey) {
      if (this.sortColumn === sortKey) {
        return this.ascending ? 'sorted asc' : 'sorted desc'
      }
    },

    sortBy: function (sortKey) {
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
.executions-log-table th  {
  cursor: pointer;
}

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

.executions-log-table .sorted:after {
  display: inline-block;
  vertical-align: middle;
  width: 0;
  height: 0;
  margin-left: 5px;
  content: ""
}

.executions-log-table .sorted.asc:after {
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 4px solid var(--font-color-main);
}

.executions-log-table .sorted.desc:after {
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid var(--font-color-main);
}
</style>

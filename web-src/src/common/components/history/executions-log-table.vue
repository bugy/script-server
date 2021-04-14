<template>
  <div class="executions-log-table">
    <table class="highlight striped">
      <thead>
      <tr>
        <th class="id-column">
          <a href="#" @click="sortBy('id')">ID<span :class="ascending ? 'arrow asc' : 'arrow desc'"></span></a>
        </th>
        <th class="start_time-column">
          <a href="#" @click="sortBy('startTimeString')">Start Time<span :class="ascending ? 'arrow asc' : 'arrow desc'"></span></a>
        </th>
        <th class="user-column">
          <a href="#" @click="sortBy('user')">User<span :class="ascending ? 'arrow asc' : 'arrow desc'"></span></a>
        </th>
        <th class="script-column">
          <a href="#" @click="sortBy('script')">Script<span :class="ascending ? 'arrow asc' : 'arrow desc'"></span></a>
        </th>
        <th class="status-column">
          <a href="#" @click="sortBy('fullStatus')">Status<span :class="ascending ? 'arrow asc' : 'arrow desc'"></span></a>
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

.executions-log-table .arrow {
  display: inline-block;
  vertical-align: middle;
  width: 0;
  height: 0;
  margin-left: 5px;
  opacity: 0.66;
}

.executions-log-table .arrow.asc {
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 4px solid #42b983;
}

.executions-log-table .arrow.desc {
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid #42b983;
}
</style>
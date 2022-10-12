<template>
  <div class="executions-log-table">
    <div class="search-container">
      <div class="search-panel">
        <input ref="searchField" autocomplete="off" class="search-field"
               name="searchField"
               placeholder="Search"
               v-model="searchText">
        <input :alt="isClearSearchButton ? 'Clear search' : 'Search'" :src="searchImage"
             class="search-button"
             type="image"
             @click="searchIconClickHandler">
      </div>
    </div>
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
      <tr v-for="row in filteredRows" :key="row.id" @click="rowClick(row)">
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
import ClearIcon from '@/assets/clear.png'
import SearchIcon from '@/assets/search.png'

export default {
  name: 'executions-log-table',
  props: {
    rows: Array,
    rowClick: {
      type: Function
    }
  },

  data() {
    return {
      searchText: '',
      sortColumn: 'id',
      ascending: false
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
    },

    searchIconClickHandler() {
      if (this.isClearSearchButton) {
        this.searchText = '';
      }
    },
  },

  computed: {
    ...mapState('history', ['loading']),

    isClearSearchButton() {
      return this.searchText !== '';
    },

    searchImage() {
      return this.isClearSearchButton ? ClearIcon : SearchIcon;
    },

    filteredRows() {
      let searchText = (this.searchText || '').trim().toLowerCase();
      let resultRows;
      if(!this.rows) {
        resultRows = [];
      } else if(searchText === '') {
        resultRows = [...this.rows];
      } else {
        resultRows = this.rows.filter((row) => {
          return row.script.toLowerCase().includes(searchText) ||
            row.user.toLowerCase().includes(searchText);
        });
      }

      let ascending = this.ascending;
      let column = this.sortColumn;

      return resultRows.sort((a, b) => {
        if (column === 'id') {
          let id_a = a[column];
          let id_b = b[column];
          return ascending ? id_a - id_b : id_b - id_a

        } else if (column === 'startTimeString') {
          let date_a = new Date(a[column]);
          let date_b = new Date(b[column]);
          return ascending ? date_a - date_b : date_b - date_a

        } else {
          let other_a = a[column].toLowerCase()
          let other_b = b[column].toLowerCase()
          if (other_a > other_b) {
            return ascending ? 1 : -1
          } else if (other_a < other_b) {
            return ascending ? -1 : 1
          }
          return 0;
        }
      });
    }
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

.search-container {
  min-width: 200px;
  width: 50%;
}

.search-panel {
  display: flex;
}

.search-button {
  align-self: center;
}
</style>

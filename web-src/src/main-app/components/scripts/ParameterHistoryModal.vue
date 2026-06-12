<template>
  <v-dialog v-model="isOpen" max-width="600" scrollable>
    <v-card class="parameter-history-modal">
      <v-card-title>Parameter History</v-card-title>
      <v-card-text>
        <div class="use-historical-values-toggle">
          <label>
            <input
              type="checkbox"
              v-model="useHistoricalValues"
              @change="saveToggleState"
            />
            <span>Use historical values as defaults</span>
          </label>
        </div>

        <div v-if="!history.length">
          <p>No parameter history available for this script.</p>
        </div>

        <div v-else>
          <div v-for="(entry, index) in history" :key="index" class="entry" :class="{ 'favorite': entry.favorite }">
            <div class="header">
              <span class="timestamp">{{ formatTimestamp(entry.timestamp) }}</span>
              <div class="header-buttons">
                <v-btn icon
                       :color="entry.favorite ? 'primary' : undefined"
                       variant="text"
                       density="compact"
                       :title="entry.favorite ? 'Remove from favorites' : 'Add to favorites'"
                       @click="toggleFavorite(index)">
                  <v-icon>{{ entry.favorite ? 'star' : 'star_border' }}</v-icon>
                </v-btn>
                <v-btn icon
                       variant="text"
                       density="compact"
                       color="success"
                       title="Use these parameters"
                       @click="useParameters(entry.values)">
                  <v-icon>play_arrow</v-icon>
                </v-btn>
                <v-btn icon
                       variant="text"
                       density="compact"
                       :disabled="entry.favorite"
                       title="Remove this entry"
                       @click="removeEntry(index)">
                  <v-icon>delete</v-icon>
                </v-btn>
              </div>
            </div>

            <div class="params">
              <div v-for="(value, paramName) in entry.values" :key="paramName" class="param">
                <span class="name">{{ paramName }}:</span>
                <span class="value">{{ formatValue(value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { loadParameterHistory, removeParameterHistoryEntry, toggleFavoriteEntry } from '@/common/utils/parameterHistory';

export default {
  name: 'ParameterHistoryModal',
  props: {
    scriptName: { type: String, required: true }
  },
  data() {
    return { history: [], useHistoricalValues: false, isOpen: false }
  },
  methods: {
    loadHistory() {
      this.history = loadParameterHistory(this.scriptName);
    },

    open() {
      this.loadHistory();
      this.loadToggleState();
      this.isOpen = true;
    },

    removeEntry(index) {
      removeParameterHistoryEntry(this.scriptName, index);
      this.loadHistory();
    },

    toggleFavorite(index) {
      toggleFavoriteEntry(this.scriptName, index);
      this.loadHistory();
    },

    useParameters(values) {
      this.$emit('use-parameters', values);
      this.isOpen = false;
    },

    formatValue(value) {
      if (value == null) return '(empty)';
      if (Array.isArray(value)) return value.join(', ');
      return String(value);
    },

    formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleString();
    },

    saveToggleState() {
      localStorage.setItem(`useHistoricalValues_${this.scriptName}`, this.useHistoricalValues);
    },

    loadToggleState() {
      this.useHistoricalValues = localStorage.getItem(`useHistoricalValues_${this.scriptName}`) === 'true';
    }
  },

  watch: {
    isOpen(val) {
      if (!val) this.$emit('close');
    }
  }
}
</script>

<style scoped>
.entry {
  border: 1px solid var(--outline-color);
  border-radius: 4px;
  margin-bottom: 12px;
  padding: 12px;
  transition: all 0.2s ease;
}

.entry.favorite {
  border-color: var(--primary-color);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--outline-color);
}

.header-buttons {
  display: flex;
  gap: 4px;
}

.timestamp {
  font-weight: bold;
  color: var(--primary-color);
}

.params {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param {
  display: flex;
  gap: 8px;
}

.name {
  font-weight: 500;
  min-width: 120px;
  color: var(--font-color-main);
}

.value {
  word-break: break-word;
}

.use-historical-values-toggle {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
</style>

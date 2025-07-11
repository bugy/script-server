<template>
  <div ref="modal" class="modal">
    <div class="modal-content">
      
      <div v-if="!history.length">
        <p>No parameter history available for this script.</p>
      </div>
      
      <div v-else>
        <div v-for="(entry, index) in history" :key="index" class="entry" :class="{ 'favorite': entry.favorite }">
          <div class="header">
            <span class="timestamp">{{ formatTimestamp(entry.timestamp) }}</span>
            <div class="header-buttons">
              <button class="btn-flat favorite-btn" 
                      @click="toggleFavorite(index)"
                      :title="entry.favorite ? 'Remove from favorites' : 'Add to favorites'"
                      :class="{ 'favorited': entry.favorite }">
                <i class="material-icons">{{ entry.favorite ? 'star' : 'star_border' }}</i>
              </button>
              <button class="btn-flat use-btn" 
                      @click="useParameters(entry.values)"
                      title="Use these parameters">
                <i class="material-icons">play_arrow</i>
              </button>
              <button class="btn-flat remove-btn" 
                      @click="removeEntry(index)"
                      title="Remove this entry"
                      :disabled="entry.favorite">
                <i class="material-icons">delete</i>
              </button>
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
    </div>
  </div>
</template>

<script>
import { loadParameterHistory, removeParameterHistoryEntry, toggleFavoriteEntry } from '@/common/utils/parameterHistory';

export default {
  name: 'ParameterHistoryModal',
  props: {
    scriptName: { type: String, required: true }
  },
  data() {
    return { history: [] }
  },
  mounted() {
    this.loadHistory();
    this.initModal();
  },
  beforeDestroy() {
    this.modalInstance?.destroy();
  },
  methods: {
    loadHistory() {
      this.history = loadParameterHistory(this.scriptName);
    },
    
    initModal() {
      if (window.M?.Modal) {
        this.modalInstance = window.M.Modal.init(this.$refs.modal, {
          onCloseEnd: () => this.$emit('close'),
          dismissible: true
        });
      }
    },
    
    open() {
      this.loadHistory();
      this.modalInstance?.open();
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
      this.modalInstance?.close();
    },
    
    formatValue(value) {
      if (value == null) return '(empty)';
      if (Array.isArray(value)) return value.join(', ');
      return String(value);
    },
    
    formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleString();
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
  background-color: rgba(var(--primary-color-rgb), 0.05);
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

.favorite-btn {
  padding: 4px;
  min-width: 32px;
  height: 32px;
  line-height: 24px;
  color: var(--font-color-secondary);
  transition: all 0.2s ease;
}

.favorite-btn.favorited {
  color: var(--primary-color);
}

.favorite-btn:hover {
  color: var(--primary-color);
}

.favorite-btn i {
  font-size: 18px;
}

.use-btn {
  padding: 4px;
  min-width: 32px;
  height: 32px;
  line-height: 24px;
  color: var(--success-color, #4caf50);
}

.use-btn i {
  font-size: 18px;
}

.remove-btn {
  padding: 4px;
  min-width: 32px;
  height: 32px;
  line-height: 24px;
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.remove-btn i {
  font-size: 18px;
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
  color: var(--font-color-secondary);
  word-break: break-word;
}
</style> 
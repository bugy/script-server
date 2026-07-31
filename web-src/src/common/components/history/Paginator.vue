<template>
  <div class="paginator-container">
    <div class="paginator-info-panel">
      <label class="page-size-label">
        <span>Per page:</span>
        <select class="browser-default page-size-select" :value="pageSize" @change="onSizeChange" :disabled="disabled">
          <option v-for="option in pageSizeOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </label>
      <span class="records-info">{{ infoText }}</span>
    </div>

    <div class="paginator-controls">
      <button class="btn-flat btn-pagination" :disabled="disabled || isFirstPage" @click="onFirst" title="First page">
        <svg viewBox="0 0 24 24" class="pagination-icon"><path d="M18.41 16.59L13.82 12l4.59-4.59L17 6l-6 6 6 6zM6 6h2v12H6z"/></svg>
      </button>
      <button class="btn-flat btn-pagination" :disabled="disabled || isFirstPage" @click="onPrev" title="Previous page">
        <svg viewBox="0 0 24 24" class="pagination-icon"><path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/></svg>
      </button>

      <span class="page-indicator">
        Page {{ page }} of {{ totalPages || 1 }}
      </span>

      <button class="btn-flat btn-pagination" :disabled="disabled || isLastPage" @click="onNext" title="Next page">
        <svg viewBox="0 0 24 24" class="pagination-icon"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
      </button>
      <button class="btn-flat btn-pagination" :disabled="disabled || isLastPage" @click="onLast" title="Last page">
        <svg viewBox="0 0 24 24" class="pagination-icon"><path d="M5.59 7.41L10.18 12l-4.59 4.59L7 18l6-6-6-6zM16 6h2v12h-2z"/></svg>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Paginator',

  props: {
    page: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 25
    },
    total: {
      type: Number,
      default: 0
    },
    totalPages: {
      type: Number,
      default: 1
    },
    pageSizeOptions: {
      type: Array,
      default: () => [10, 25, 50, 100, 250, 500]
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },

  computed: {
    startRecord() {
      if (this.total === 0) return 0;
      return (this.page - 1) * this.pageSize + 1;
    },

    endRecord() {
      if (this.total === 0) return 0;
      return Math.min(this.page * this.pageSize, this.total);
    },

    infoText() {
      if (this.total === 0) {
        return 'No entries';
      }
      return `Showing ${this.startRecord} - ${this.endRecord} of ${this.total} entries`;
    },

    isFirstPage() {
      return this.page <= 1;
    },

    isLastPage() {
      return this.page >= this.totalPages || this.totalPages === 0;
    }
  },

  methods: {
    onSizeChange(event) {
      const newSize = parseInt(event.target.value, 10);
      this.$emit('size-change', newSize);
    },

    onFirst() {
      if (!this.isFirstPage) {
        this.$emit('page-change', 1);
      }
    },

    onPrev() {
      if (!this.isFirstPage) {
        this.$emit('page-change', this.page - 1);
      }
    },

    onNext() {
      if (!this.isLastPage) {
        this.$emit('page-change', this.page + 1);
      }
    },

    onLast() {
      if (!this.isLastPage) {
        this.$emit('page-change', this.totalPages);
      }
    }
  }
};
</script>

<style scoped>
.paginator-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 0.8rem 0;
  margin-top: 1rem;
  border-top: 1px solid var(--border-color, #e0e0e0);
  font-size: 0.95rem;
  color: var(--font-color-main, #333);
}

.paginator-info-panel {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  flex-wrap: wrap;
}

.page-size-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  color: var(--font-color-main, #333);
  margin: 0;
}

.page-size-select {
  display: inline-block;
  width: auto;
  height: 2rem;
  padding: 0 0.5rem;
  border: 1px solid var(--border-color, #ccc);
  border-radius: 4px;
  background-color: var(--background-color-secondary, #fff);
  color: var(--font-color-main, #333);
  cursor: pointer;
}

.records-info {
  color: var(--font-color-medium, #666);
}

.paginator-controls {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-pagination {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.5rem;
  min-width: 2.2rem;
  height: 2.2rem;
  border-radius: 4px;
  border: 1px solid var(--border-color, #ccc);
  background-color: var(--background-color-secondary, #fff);
  color: var(--font-color-main, #333);
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, opacity 0.2s ease;
}

.pagination-icon {
  width: 1.2rem;
  height: 1.2rem;
  fill: currentColor;
}

.btn-pagination:hover:not(:disabled) {
  background-color: var(--primary-color-light, #e3f2fd);
  border-color: var(--primary-color, #2196f3);
  color: var(--primary-color, #2196f3);
}

.btn-pagination:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.page-indicator {
  padding: 0 0.6rem;
  font-weight: 500;
  color: var(--font-color-main, #333);
}
</style>

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
        «
      </button>
      <button class="btn-flat btn-pagination" :disabled="disabled || isFirstPage" @click="onPrev" title="Previous page">
        ‹ Prev
      </button>

      <span class="page-indicator">
        Page {{ page }} of {{ totalPages || 1 }}
      </span>

      <button class="btn-flat btn-pagination" :disabled="disabled || isLastPage" @click="onNext" title="Next page">
        Next ›
      </button>
      <button class="btn-flat btn-pagination" :disabled="disabled || isLastPage" @click="onLast" title="Last page">
        »
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
  padding: 0.3rem 0.7rem;
  height: auto;
  line-height: normal;
  border-radius: 4px;
  border: 1px solid var(--border-color, #ccc);
  background-color: var(--background-color-secondary, #fff);
  color: var(--font-color-main, #333);
  cursor: pointer;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.btn-pagination:hover:not(:disabled) {
  background-color: var(--primary-color-light, #e3f2fd);
  border-color: var(--primary-color, #2196f3);
  color: var(--primary-color, #2196f3);
}

.btn-pagination:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-indicator {
  padding: 0 0.6rem;
  font-weight: 500;
  color: var(--font-color-main, #333);
}
</style>

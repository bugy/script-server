<template>
  <div 
    v-if="failedItems.scripts.length"
    class="script-list-group script-list-failed-group" 
    @click="$emit('group-clicked', failedItems.name)">
    <div 
      class="collection-item waves-effect script-group script-failed-group">
      <span>{{failedItems.name}}</span>
      <i class="material-icons">
        {{ failedItems.isActive ? 'expand_less' : 'expand_more' }}
      </i>
    </div>
    <template v-for="item in failedItems.scripts" v-if="failedItems.isActive">
      <div class="collection-item script-list-item script-list-failed-item">
          {{ item.path }}
      </div>
    </template>
  </div>
</template>

<script>
import ScriptListItem from './ScriptListItem';

export default {
  name: 'ScriptListGroup',
  components: {ScriptListItem},
  props: {
    failedItems: {
      type: Object
    }
  }
}
</script>

<style scoped>
    @import "./ScriptListGroup.css";
    .script-failed-group {
      color: var(--error-color);
    }
    div.script-list-failed-item {
      padding-top:    4px;
      padding-bottom: 4px;
    }
</style>